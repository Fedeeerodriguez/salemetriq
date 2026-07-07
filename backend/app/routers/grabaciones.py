"""Router de grabaciones de llamadas + análisis IA.

- Ingesta desde Fathom (y futuros proveedores) → tabla call_recordings.
- Listado en formato tarjetas para el frontend (Call Analysis).
- Análisis IA on-demand de una grabación con Claude → tabla analysis_runs.
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..services.adapters import normalizar
from ..services.analista_ia import analizar_transcript
from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["grabaciones"])


# ── Motor de análisis (reusado por análisis manual y auto-análisis) ──────────
def _persistir_analisis(sb, rec: dict) -> dict:
    """Corre el analista IA sobre una grabación y guarda el run. Devuelve el run.

    Propaga is_demo de la grabación al análisis para respetar el aislamiento.
    Lanza RuntimeError si el modelo/API falla (deja la grabación en 'error').
    """
    rec_id = rec["id"]
    sb.table("call_recordings").update({"status": "analizando"}).eq("id", rec_id).execute()
    try:
        data = analizar_transcript(rec.get("transcript") or "", contexto=rec.get("title"))
    except RuntimeError:
        sb.table("call_recordings").update({"status": "error"}).eq("id", rec_id).execute()
        raise

    dims = data.get("dimensiones", {})
    # Fallback: si el modelo no devolvió score_global, promediar las dimensiones.
    score = data.get("score_global")
    if score is None and dims:
        vals = [v for v in dims.values() if isinstance(v, (int, float))]
        score = round(sum(vals) / len(vals), 1) if vals else None
    run_payload = {
        "target_tipo": "call_recording",
        "target_id": rec_id,
        "modelo": settings.ANTHROPIC_MODEL,
        "score": score,
        "sentiment": data.get("sentiment"),
        "objeciones": data.get("objeciones"),
        "tags": list(dims.keys()) if dims else None,
        "resumen": data.get("resumen"),
        "raw": data,
        "is_demo": bool(rec.get("is_demo")),
        "team_id": rec.get("team_id"),
    }
    inserted = sb.table("analysis_runs").insert(run_payload).execute().data
    sb.table("call_recordings").update({"status": "analizado"}).eq("id", rec_id).execute()
    return inserted[0] if inserted else run_payload


def _auto_analizar(rec_id: str) -> None:
    """Tarea de fondo: analiza una grabación recién ingestada, si hay API key."""
    if not settings.ANTHROPIC_API_KEY:
        logger.info("Auto-análisis omitido (sin ANTHROPIC_API_KEY): %s", rec_id)
        return
    sb = get_supabase_admin()
    rec = (
        sb.table("call_recordings").select("id, title, transcript, is_demo, team_id")
        .eq("id", rec_id).limit(1).execute().data
    )
    rec = rec[0] if rec else None
    if not rec or not rec.get("transcript"):
        return
    try:
        _persistir_analisis(sb, rec)
        logger.info("Auto-análisis OK: %s", rec_id)
    except Exception as e:  # noqa: BLE001 — no queremos tumbar la ingesta
        logger.warning("Auto-análisis falló para %s: %s", rec_id, e)


# ── Ingesta (webhook de Fathom) ──────────────────────────────────────────────
@router.post("/ingest/{provider}")
def ingest(
    provider: str,
    payload: dict,
    background: BackgroundTasks,
    x_ingest_key: str | None = Header(default=None),
) -> dict:
    """Recibe el payload de un proveedor (fathom, …), lo normaliza y hace upsert.

    Al terminar la llamada, el closer manda el transcript acá automáticamente y se
    dispara el análisis IA en segundo plano (busca mejoras). Protegido con
    INGEST_INTERNAL_KEY (header X-Ingest-Key) si está configurada.
    """
    if settings.INGEST_INTERNAL_KEY and x_ingest_key != settings.INGEST_INTERNAL_KEY:
        raise HTTPException(status_code=401, detail="X-Ingest-Key inválida")

    try:
        row = normalizar(provider, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    row = {k: v for k, v in row.items() if v is not None}
    sb = get_supabase_admin()
    res = sb.table("call_recordings").upsert(row, on_conflict="provider,external_id").execute()
    grabacion = res.data[0] if res.data else None

    # Auto-análisis en segundo plano si la grabación trae transcript.
    if grabacion and grabacion.get("transcript"):
        background.add_task(_auto_analizar, grabacion["id"])

    return {"ok": True, "id": grabacion.get("id") if grabacion else None, "auto_analisis": bool(grabacion and grabacion.get("transcript"))}


# ── Listado (tarjetas) ───────────────────────────────────────────────────────
@router.get("")
def listar(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    team = user.get("team_id")
    if not team:
        return []
    recs = (
        sb.table("call_recordings")
        .select("id, provider, title, recorded_at, duration_seg, status, participants")
        .eq("team_id", team)
        .order("recorded_at", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    if not recs:
        return []

    # Adjuntar el score del último análisis de cada grabación.
    ids = [r["id"] for r in recs]
    runs = (
        sb.table("analysis_runs")
        .select("target_id, score, sentiment, created_at")
        .eq("target_tipo", "call_recording")
        .in_("target_id", ids)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    ultimo: dict[str, dict] = {}
    for run in runs:
        ultimo.setdefault(run["target_id"], run)  # el primero es el más reciente

    for r in recs:
        run = ultimo.get(r["id"])
        r["score"] = run.get("score") if run else None
        r["sentiment"] = run.get("sentiment") if run else None
    return recs


# ── Detalle (transcript + último análisis) ───────────────────────────────────
@router.get("/{rec_id}")
def detalle(rec_id: str, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    res = (
        sb.table("call_recordings").select("*")
        .eq("id", rec_id).eq("team_id", user.get("team_id")).limit(1).execute()
    )
    rec = res.data[0] if res.data else None
    if not rec:
        raise HTTPException(status_code=404, detail="Grabación no encontrada")

    run = (
        sb.table("analysis_runs")
        .select("*")
        .eq("target_tipo", "call_recording")
        .eq("target_id", rec_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    rec["analisis"] = run[0] if run else None
    return rec


# ── Análisis IA on-demand ────────────────────────────────────────────────────
class AnalyzeResponse(BaseModel):
    ok: bool
    analisis: dict


@router.post("/{rec_id}/analyze", response_model=AnalyzeResponse)
def analizar(rec_id: str, user: dict = Depends(get_current_user)) -> AnalyzeResponse:
    sb = get_supabase_admin()
    res = (
        sb.table("call_recordings").select("id, title, transcript, is_demo, team_id")
        .eq("id", rec_id).eq("team_id", user.get("team_id")).limit(1).execute()
    )
    rec = res.data[0] if res.data else None
    if not rec:
        raise HTTPException(status_code=404, detail="Grabación no encontrada")
    if not rec.get("transcript"):
        raise HTTPException(status_code=400, detail="La grabación no tiene transcript para analizar")

    try:
        run = _persistir_analisis(sb, rec)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AnalyzeResponse(ok=True, analisis=run)
