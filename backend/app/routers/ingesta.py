"""Router de ingesta — entrada de transcripts (closers) y resúmenes (setters).

Pensado para ser consumido por un proceso externo (n8n, Zapier, un webhook de la
plataforma de llamadas). Se protege con una key compartida en el header
`X-Ingest-Key` cuando `INGEST_INTERNAL_KEY` está configurada.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/ingesta", tags=["ingesta"])


def _check_key(x_ingest_key: str | None) -> None:
    expected = settings.INGEST_INTERNAL_KEY
    if expected and x_ingest_key != expected:
        raise HTTPException(status_code=401, detail="X-Ingest-Key inválida")


class CallIn(BaseModel):
    closer_id: str
    fecha: str | None = None            # ISO8601; si falta, la BD usa now()
    duracion_seg: int | None = None
    outcome: str | None = None          # p.ej. "cerro", "no_cerro", "seguimiento"
    deal_value: float | None = None
    transcript: str
    lead_id: str | None = None


class SetterSummaryIn(BaseModel):
    setter_id: str
    fecha: str | None = None
    tipo: str = "texto"                  # "texto" | "audio"
    texto: str | None = None
    audio_url: str | None = None
    lead_qualification: str | None = None
    agendado: bool | None = None
    lead_id: str | None = None


@router.post("/call")
def ingest_call(body: CallIn, x_ingest_key: str | None = Header(default=None)) -> dict:
    _check_key(x_ingest_key)
    sb = get_supabase_admin()
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    res = sb.table("calls").insert(payload).execute()
    row = res.data[0] if res.data else None
    return {"ok": True, "id": row.get("id") if row else None}


@router.post("/setter-summary")
def ingest_setter_summary(body: SetterSummaryIn, x_ingest_key: str | None = Header(default=None)) -> dict:
    _check_key(x_ingest_key)
    sb = get_supabase_admin()
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    res = sb.table("setter_summaries").insert(payload).execute()
    row = res.data[0] if res.data else None
    return {"ok": True, "id": row.get("id") if row else None}
