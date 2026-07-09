"""Router del LEAD MAGNET (prueba gratuita) — PÚBLICO, sin auth.

Flujo del funnel:
  1) La landing captura email + teléfono         → POST /api/leadmagnet/registro  → { token }
  2) La página de prueba analiza UNA llamada       → POST /api/leadmagnet/analizar  → análisis IA
  3) (comercial) el dueño ve los leads capturados  → GET  /api/leadmagnet/admin/leads (superadmin)

El análisis reutiliza el MISMO motor que la plataforma (services.analista_ia),
así el prospecto prueba exactamente el producto real.
"""
import logging
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from ..services.analista_ia import analizar_transcript
from ..services.auth import require_superadmin
from ..services.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leadmagnet", tags=["leadmagnet"])

MIN_TRANSCRIPT = 200      # menos que esto no da para analizar nada útil
MAX_TRANSCRIPT = 60_000   # techo de seguridad (costo API)


class RegistroRequest(BaseModel):
    email: EmailStr
    telefono: str
    origen: str | None = None

    @field_validator("telefono")
    @classmethod
    def _tel(cls, v: str) -> str:
        v = (v or "").strip()
        # Dígitos, con + y separadores. Al menos 7 dígitos.
        if len(re.sub(r"\D", "", v)) < 7:
            raise ValueError("Teléfono inválido")
        return v


class AnalizarRequest(BaseModel):
    token: str
    transcript: str


def _lead_por_token(sb, token: str) -> dict:
    rows = sb.table("trial_leads").select("*").eq("token", token).limit(1).execute().data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Acceso de prueba inválido. Registrate de nuevo.")
    return rows[0]


@router.post("/registro")
def registro(body: RegistroRequest) -> dict:
    """Captura el lead y devuelve el token de acceso a la prueba.

    Idempotente por email: si ya existe, reutiliza su token (1 prueba por persona).
    """
    sb = get_supabase_admin()
    email = str(body.email).lower().strip()

    existente = sb.table("trial_leads").select("token, analisis_usados, max_analisis").ilike("email", email).limit(1).execute().data
    if existente:
        e = existente[0]
        # Actualiza el teléfono por si cambió, no resetea el cupo.
        sb.table("trial_leads").update({"telefono": body.telefono}).eq("token", e["token"]).execute()
        return {
            "token": e["token"],
            "ya_registrado": True,
            "analisis_restantes": max(0, (e.get("max_analisis") or 1) - (e.get("analisis_usados") or 0)),
        }

    token = "trial_" + secrets.token_urlsafe(24)
    sb.table("trial_leads").insert({
        "email": email, "telefono": body.telefono.strip(),
        "token": token, "origen": body.origen,
    }).execute()
    logger.info("Lead magnet: nuevo lead %s", email)
    return {"token": token, "ya_registrado": False, "analisis_restantes": 1}


@router.get("/estado")
def estado(token: str) -> dict:
    sb = get_supabase_admin()
    lead = _lead_por_token(sb, token)
    return {
        "email": lead["email"],
        "analisis_restantes": max(0, (lead.get("max_analisis") or 1) - (lead.get("analisis_usados") or 0)),
        "ultimo_analisis": lead.get("ultimo_analisis"),
    }


@router.post("/analizar")
def analizar(body: AnalizarRequest) -> dict:
    """Analiza UNA llamada contra el método y consume el cupo de la prueba."""
    sb = get_supabase_admin()
    lead = _lead_por_token(sb, body.token)

    usados = lead.get("analisis_usados") or 0
    maximo = lead.get("max_analisis") or 1
    if usados >= maximo:
        # Cupo agotado — devolvemos el último análisis para no perder el "wow".
        raise HTTPException(
            status_code=403,
            detail="Ya usaste tu análisis gratuito. Agendá una llamada para desbloquear tu equipo completo.",
        )

    t = (body.transcript or "").strip()
    if len(t) < MIN_TRANSCRIPT:
        raise HTTPException(status_code=400, detail=f"Pegá una transcripción más larga (mínimo {MIN_TRANSCRIPT} caracteres).")
    if len(t) > MAX_TRANSCRIPT:
        t = t[:MAX_TRANSCRIPT]

    try:
        analisis = analizar_transcript(t, contexto="Prueba gratuita del lead magnet.")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    sb.table("trial_leads").update({
        "analisis_usados": usados + 1,
        "ultimo_analisis": analisis,
    }).eq("token", body.token).execute()

    return {"analisis": analisis, "analisis_restantes": max(0, maximo - (usados + 1))}


@router.get("/admin/leads")
def listar_leads(_: dict = Depends(require_superadmin)) -> list[dict]:
    """Leads capturados por el funnel (para seguimiento comercial). Solo superadmin."""
    sb = get_supabase_admin()
    rows = (
        sb.table("trial_leads").select("email, telefono, analisis_usados, origen, created_at")
        .order("created_at", desc=True).limit(500).execute().data or []
    )
    return rows
