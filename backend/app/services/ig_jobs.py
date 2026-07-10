"""Runner de un scrape_job: collector → scoring → dedup → guarda.

Se ejecuta en background (FastAPI BackgroundTasks). Va marcando el estado del job
en la DB para que el frontend muestre el progreso (pendiente → corriendo → ok/error).
"""
import logging

from . import clasificador_ia, collector, dedup, scoring
from .supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

# Tope de perfiles a clasificar con IA por job (control de costo/latencia).
_MAX_IA = 40


def _nicho(sb, nicho_id: str | None) -> dict | None:
    if not nicho_id:
        return None
    res = sb.table("nichos").select("*").eq("id", nicho_id).limit(1).execute()
    return res.data[0] if res.data else None


def run_job(job_id: str) -> None:
    """Corre el job completo. No propaga excepciones: las guarda en el job."""
    sb = get_supabase_admin()
    try:
        res = sb.table("scrape_jobs").select("*").eq("id", job_id).limit(1).execute()
        job = res.data[0] if res.data else None
        if not job:
            logger.error("run_job: job %s no existe", job_id)
            return

        sb.table("scrape_jobs").update({"estado": "corriendo"}).eq("id", job_id).execute()

        nicho = _nicho(sb, job.get("nicho_id"))
        perfiles = collector.buscar(job["angulo"], job["query"], job.get("filtros") or {})

        # Puntuar y aplicar filtro de score mínimo si vino en filtros.
        filtros = job.get("filtros") or {}
        min_score = int(filtros.get("min_score") or 0)
        scores: dict[str, int] = {}
        elegidos = []
        for p in perfiles:
            s = scoring.score(p, nicho, job.get("query", ""))
            if s >= min_score and _pasa_filtros(p, filtros):
                scores[p["username"]] = s
                p["score_nicho"] = s  # que el clasificador vea el score
                elegidos.append(p)

        # Fase 4 — clasificador IA (si el nicho lo activa). Prioriza mayor score.
        if nicho and nicho.get("usa_ia") and elegidos:
            for p in sorted(elegidos, key=lambda x: x.get("score_nicho", 0), reverse=True)[:_MAX_IA]:
                res_ia = clasificador_ia.clasificar(p, nicho)
                if res_ia:
                    p["ia_veredicto"], p["ia_motivo"] = res_ia

        total, nuevos = dedup.upsert_perfiles(elegidos, job.get("nicho_id"), scores)

        sb.table("scrape_jobs").update({
            "estado": "ok",
            "total_encontrados": total,
            "total_nuevos": nuevos,
        }).eq("id", job_id).execute()
        logger.info("Job %s OK — %s perfiles (%s nuevos)", job_id, total, nuevos)

    except Exception as e:  # noqa: BLE001 — queremos registrar cualquier fallo en el job
        logger.exception("Job %s falló", job_id)
        try:
            sb.table("scrape_jobs").update({
                "estado": "error",
                "error_msg": str(e)[:500],
            }).eq("id", job_id).execute()
        except Exception:
            logger.exception("No se pudo marcar el job %s como error", job_id)


def _pasa_filtros(perfil: dict, filtros: dict) -> bool:
    """Filtros numéricos/booleanos aplicados post-scraping."""
    f = filtros or {}
    followers = perfil.get("followers")
    if f.get("min_followers") and (followers or 0) < int(f["min_followers"]):
        return False
    if f.get("max_followers") and (followers or 0) > int(f["max_followers"]):
        return False
    if f.get("solo_business") and not perfil.get("is_business"):
        return False
    if f.get("con_contacto") and not (perfil.get("email_publico") or perfil.get("external_url")):
        return False
    return True
