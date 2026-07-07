"""Router de Fathom — Fase F: ingesta real de llamadas de closers.

Cuando Fathom termina de procesar una llamada, dispara el webhook
"new meeting content ready" hacia la URL que el admin registró:

    https://TU-BACKEND/api/fathom/webhook?token=<fathom_token-del-workspace>

El token identifica el workspace (multi-tenant). Dentro de ese workspace se
atribuye la grabación al closer cuyo email coincide con el host de la llamada
(fathom_email override, si no, el email de login). Si ningún closer matchea, la
grabación igual se guarda en el workspace como "sin asignar" para que el admin la
reasigne. Luego se dispara el análisis IA en segundo plano (coaching).
"""
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from ..services.adapters import normalizar as normalizar_provider
from ..services.adapters.fathom import host_email, invitee_emails
from ..services.supabase_client import get_supabase_admin
from .grabaciones import _auto_analizar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fathom", tags=["fathom"])


def _resolver_team(sb, token: str) -> dict | None:
    if not token:
        return None
    res = sb.table("teams").select("id, is_demo").eq("fathom_token", token).limit(1).execute().data
    return res[0] if res else None


def _resolver_closer(sb, team_id: str, emails: list[str]) -> str | None:
    """Busca un closer del workspace cuyo email (o fathom_email) esté en `emails`."""
    emails = [e for e in emails if e]
    if not emails:
        return None
    closers = (
        sb.table("users").select("id, email, fathom_email")
        .eq("team_id", team_id).eq("rol", "closer").eq("activo", True).execute().data or []
    )
    lookup: dict[str, str] = {}
    for c in closers:
        if c.get("email"):
            lookup[c["email"].lower()] = c["id"]
        if c.get("fathom_email"):
            lookup[c["fathom_email"].lower()] = c["id"]
    for e in emails:
        if e in lookup:
            return lookup[e]
    return None


@router.post("/webhook")
async def webhook(request: Request, background: BackgroundTasks, token: str = "") -> dict:
    sb = get_supabase_admin()
    team = _resolver_team(sb, token)
    if not team:
        raise HTTPException(status_code=401, detail="Token de workspace inválido")

    payload = await request.json()
    row = normalizar_provider("fathom", payload)  # agrega provider + raw

    # Atribución: primero el host, luego cualquier invitado que sea closer.
    host = host_email(payload)
    candidatos = ([host] if host else []) + invitee_emails(payload)
    closer_id = _resolver_closer(sb, team["id"], candidatos)

    row["team_id"] = team["id"]
    row["is_demo"] = bool(team.get("is_demo"))
    if closer_id:
        row["closer_id"] = closer_id

    row = {k: v for k, v in row.items() if v is not None}
    res = sb.table("call_recordings").upsert(row, on_conflict="provider,external_id").execute()
    grabacion = res.data[0] if res.data else None

    tiene_transcript = bool(grabacion and grabacion.get("transcript"))
    if tiene_transcript:
        background.add_task(_auto_analizar, grabacion["id"])

    if not closer_id:
        logger.warning(
            "Fathom: grabación %s sin closer asignado (host=%s) en team %s",
            grabacion.get("id") if grabacion else "?", host, team["id"],
        )

    return {
        "ok": True,
        "id": grabacion.get("id") if grabacion else None,
        "closer_asignado": bool(closer_id),
        "auto_analisis": tiene_transcript,
    }
