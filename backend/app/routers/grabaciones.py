"""Router de grabaciones de llamadas + análisis IA.

- Ingesta desde Fathom (y futuros proveedores) → tabla call_recordings.
- Listado en formato tarjetas para el frontend (Call Analysis).
- Análisis IA on-demand de una grabación con Claude → tabla analysis_runs.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..services.adapters import normalizar
from ..services.analista_ia import analizar_transcript
from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["grabaciones"])


# ── Ingesta (webhook de Fathom) ──────────────────────────────────────────────
@router.post("/ingest/{provider}")
def ingest(provider: str, payload: dict, x_ingest_key: str | None = Header(default=None)) -> dict:
    """Recibe el payload de un proveedor (fathom, …), lo normaliza y hace upsert.

    Protegido con INGEST_INTERNAL_KEY (header X-Ingest-Key) si está configurada.
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
    return {"ok": True, "id": grabacion.get("id") if grabacion else None}


# ── Listado (tarjetas) ───────────────────────────────────────────────────────
@router.get("")
def listar(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    recs = (
        sb.table("call_recordings")
        .select("id, provider, title, recorded_at, duration_seg, status, participants")
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
    res = sb.table("call_recordings").select("*").eq("id", rec_id).limit(1).execute()
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
    res = sb.table("call_recordings").select("id, title, transcript").eq("id", rec_id).limit(1).execute()
    rec = res.data[0] if res.data else None
    if not rec:
        raise HTTPException(status_code=404, detail="Grabación no encontrada")
    if not rec.get("transcript"):
        raise HTTPException(status_code=400, detail="La grabación no tiene transcript para analizar")

    sb.table("call_recordings").update({"status": "analizando"}).eq("id", rec_id).execute()
    try:
        data = analizar_transcript(rec["transcript"], contexto=rec.get("title"))
    except RuntimeError as e:
        sb.table("call_recordings").update({"status": "error"}).eq("id", rec_id).execute()
        raise HTTPException(status_code=502, detail=str(e))

    dims = data.get("dimensiones", {})
    run_payload = {
        "target_tipo": "call_recording",
        "target_id": rec_id,
        "modelo": settings.ANTHROPIC_MODEL,
        "score": data.get("score_global"),
        "sentiment": data.get("sentiment"),
        "objeciones": data.get("objeciones"),
        "tags": list(dims.keys()) if dims else None,
        "resumen": data.get("resumen"),
        "raw": data,
    }
    inserted = sb.table("analysis_runs").insert(run_payload).execute().data
    sb.table("call_recordings").update({"status": "analizado"}).eq("id", rec_id).execute()
    return AnalyzeResponse(ok=True, analisis=inserted[0] if inserted else run_payload)
