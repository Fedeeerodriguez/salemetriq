"""Router de Coaching — resúmenes por closer y diagnóstico general del equipo.

Agrega los análisis (analysis_runs.raw) de las grabaciones del workspace y calcula:
- promedio por etapa del método,
- adopción de cada técnica del método (% de llamadas que la usaron),
- fugas recurrentes (mejoras por etapa),
y le pide a Claude una narrativa de coaching anclada al método.

Todo scopeado por team_id (multi-tenant).
"""
import json

from fastapi import APIRouter, Depends, HTTPException

from ..services.analista_ia import ETAPAS, narrativa_coaching
from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/coaching", tags=["coaching"])

# Etiquetas legibles para el checklist de técnicas del método.
CHECK_LABELS = {
    "uso_especificamente": "Pregunta el outcome 'específicamente'",
    "outcome_definido": "Define el resultado deseado",
    "urgencia_tiempo": "Construye urgencia con el tiempo",
    "motivo_emocional_profundo": "Llega al motivo emocional profundo",
    "tres_creencias": "Chequea las 3 creencias (posib./capac./merec.)",
    "lenguaje_cuando_yo_te_lleve": "Lenguaje 'cuando YO te lleve'",
    "profundizo_visualizacion": "Profundiza la visualización",
    "reality_check": "Hace el Reality Check antes del miedo",
    "como_te_harias_sentir": "Usa '¿cómo te harías sentir?'",
    "pregunta_del_control": "Pregunta del control (→ 'yo')",
    "micro_compromiso_pre_pitch": "Micro-compromiso antes del pitch",
    "pitch_que_porque_como": "Pitch con QUÉ/POR QUÉ/CÓMO",
    "objeciones_orden_correcto": "Objeciones en orden (finanzas→logística→miedo)",
    "asumio_cierre": "Asume el cierre",
    "tie_down": "Usa tie-downs de compromiso",
}


def _runs_de(sb, team: str, closer_id: str | None = None) -> list[dict]:
    """Trae los análisis de grabaciones del team (opcionalmente de un closer)."""
    recs_q = sb.table("call_recordings").select("id, closer_id").eq("team_id", team)
    if closer_id:
        recs_q = recs_q.eq("closer_id", closer_id)
    recs = recs_q.execute().data or []
    rec_closer = {r["id"]: r.get("closer_id") for r in recs}
    if not rec_closer:
        return []
    runs = (
        sb.table("analysis_runs").select("target_id, score, raw, created_at")
        .eq("team_id", team).eq("target_tipo", "call_recording")
        .in_("target_id", list(rec_closer.keys()))
        .order("created_at", desc=True).execute().data or []
    )
    for r in runs:
        r["closer_id"] = rec_closer.get(r["target_id"])
    return runs


def _agregar(runs: list[dict]) -> dict:
    """Calcula promedios por etapa, adopción de técnicas y fugas recurrentes."""
    n = len(runs)
    if not n:
        return {"n": 0}
    # score global
    scores = [r["score"] for r in runs if r.get("score") is not None]
    score_prom = round(sum(scores) / len(scores)) if scores else None
    # promedio por etapa
    etapas_acc: dict[str, list] = {e: [] for e in ETAPAS}
    check_acc: dict[str, list] = {}
    mejoras_por_etapa: dict[str, int] = {}
    ejemplos: list[dict] = []
    for r in runs:
        raw = r.get("raw") or {}
        dims = raw.get("dimensiones") or {}
        for e in ETAPAS:
            v = dims.get(e)
            if isinstance(v, (int, float)):
                etapas_acc[e].append(v)
        for k, v in (raw.get("checklist") or {}).items():
            check_acc.setdefault(k, []).append(1 if v else 0)
        for m in raw.get("mejoras") or []:
            et = m.get("etapa") or "general"
            mejoras_por_etapa[et] = mejoras_por_etapa.get(et, 0) + 1
            if m.get("prioridad") == "alta" and len(ejemplos) < 6:
                ejemplos.append({"etapa": et, "accion": m.get("accion"), "ejemplo": m.get("ejemplo")})

    etapas_prom = {e: (round(sum(v) / len(v)) if v else None) for e, v in etapas_acc.items()}
    checklist = [
        {"key": k, "label": CHECK_LABELS.get(k, k), "pct": round(sum(v) / len(v) * 100)}
        for k, v in check_acc.items() if v
    ]
    checklist.sort(key=lambda x: x["pct"])  # las menos usadas primero (donde falla)
    # etapa más débil (menor promedio)
    validas = {e: s for e, s in etapas_prom.items() if s is not None}
    etapa_debil = min(validas, key=validas.get) if validas else None

    return {
        "n": n,
        "score_prom": score_prom,
        "etapas_prom": etapas_prom,
        "etapa_debil": etapa_debil,
        "checklist": checklist,
        "mejoras_por_etapa": mejoras_por_etapa,
        "ejemplos_mejora": ejemplos,
    }


@router.get("/closer/{closer_id}")
def coaching_closer(closer_id: str, user: dict = Depends(get_current_user)) -> dict:
    team = user.get("team_id")
    if not team:
        raise HTTPException(status_code=404, detail="Sin workspace")
    sb = get_supabase_admin()
    u = (
        sb.table("users").select("id, nombre, email")
        .eq("id", closer_id).eq("team_id", team).limit(1).execute().data
    )
    if not u:
        raise HTTPException(status_code=404, detail="Closer no encontrado en tu workspace")
    agg = _agregar(_runs_de(sb, team, closer_id))
    narrativa = None
    if agg.get("n"):
        datos = {"closer": u[0]["nombre"], **{k: agg[k] for k in
                 ["n", "score_prom", "etapas_prom", "checklist", "mejoras_por_etapa", "ejemplos_mejora"]}}
        narrativa = narrativa_coaching(json.dumps(datos, ensure_ascii=False), "closer")
    return {"closer": {"id": u[0]["id"], "nombre": u[0]["nombre"]}, "narrativa": narrativa, **agg}


@router.get("/equipo")
def coaching_equipo(user: dict = Depends(get_current_user)) -> dict:
    team = user.get("team_id")
    if not team:
        raise HTTPException(status_code=404, detail="Sin workspace")
    sb = get_supabase_admin()
    runs = _runs_de(sb, team)
    agg = _agregar(runs)

    # Ranking por closer (score promedio).
    por_closer: dict[str, list] = {}
    for r in runs:
        if r.get("closer_id") and r.get("score") is not None:
            por_closer.setdefault(r["closer_id"], []).append(r["score"])
    nombres = {}
    if por_closer:
        us = sb.table("users").select("id, nombre").in_("id", list(por_closer.keys())).execute().data or []
        nombres = {u["id"]: u["nombre"] for u in us}
    ranking = sorted(
        ({"closer_id": cid, "nombre": nombres.get(cid, "—"),
          "score_prom": round(sum(s) / len(s)), "llamadas": len(s)} for cid, s in por_closer.items()),
        key=lambda x: x["score_prom"], reverse=True,
    )

    narrativa = None
    if agg.get("n"):
        datos = {**{k: agg[k] for k in
                 ["n", "score_prom", "etapas_prom", "etapa_debil", "checklist", "mejoras_por_etapa"]},
                 "ranking_closers": ranking}
        narrativa = narrativa_coaching(json.dumps(datos, ensure_ascii=False), "equipo")

    return {"narrativa": narrativa, "ranking": ranking, **agg}
