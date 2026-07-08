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


def _resolver_destino(sb, token: str) -> dict | None:
    """Resuelve a qué workspace (y opcionalmente closer) pertenece el token.

    - token de USUARIO (fathom_user_token) → atribuye directo a ese closer.
    - token de WORKSPACE (teams.fathom_token) → atribuye por email del host.
    Devuelve {team_id, is_demo, closer_id?} o None si el token no existe.
    """
    if not token:
        return None
    u = (
        sb.table("users").select("id, team_id, is_demo")
        .eq("fathom_user_token", token).limit(1).execute().data
    )
    if u:
        return {"team_id": u[0]["team_id"], "is_demo": bool(u[0].get("is_demo")), "closer_id": u[0]["id"]}
    t = sb.table("teams").select("id, is_demo").eq("fathom_token", token).limit(1).execute().data
    if t:
        return {"team_id": t[0]["id"], "is_demo": bool(t[0].get("is_demo")), "closer_id": None}
    return None


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
    destino = _resolver_destino(sb, token)
    if not destino:
        raise HTTPException(status_code=401, detail="Token inválido")

    payload = await request.json()
    row = normalizar_provider("fathom", payload)  # agrega provider + raw

    # Atribución: si el token es de un usuario, va directo a él. Si es de workspace,
    # se resuelve por el email del host (o invitados closer).
    closer_id = destino.get("closer_id")
    host = host_email(payload)
    if not closer_id:
        candidatos = ([host] if host else []) + invitee_emails(payload)
        closer_id = _resolver_closer(sb, destino["team_id"], candidatos)

    row["team_id"] = destino["team_id"]
    row["is_demo"] = destino["is_demo"]
    if closer_id:
        row["closer_id"] = closer_id

    # Aislamiento: la clave única (provider, external_id) es global. Antes de
    # upsertear, si ya existe una grabación con ese external_id en OTRO workspace,
    # rechazamos — así un webhook no puede pisar/robar la grabación de otro team.
    if row.get("external_id"):
        existente = (
            sb.table("call_recordings").select("id, team_id")
            .eq("provider", "fathom").eq("external_id", row["external_id"]).limit(1).execute().data
        )
        if existente and existente[0].get("team_id") not in (None, destino["team_id"]):
            raise HTTPException(status_code=409, detail="La grabación pertenece a otro workspace")

    row = {k: v for k, v in row.items() if v is not None}
    res = sb.table("call_recordings").upsert(row, on_conflict="provider,external_id").execute()
    grabacion = res.data[0] if res.data else None

    tiene_transcript = bool(grabacion and grabacion.get("transcript"))
    if tiene_transcript:
        background.add_task(_auto_analizar, grabacion["id"])

    if not closer_id:
        logger.warning(
            "Fathom: grabación %s sin closer asignado (host=%s) en team %s",
            grabacion.get("id") if grabacion else "?", host, destino["team_id"],
        )

    return {
        "ok": True,
        "id": grabacion.get("id") if grabacion else None,
        "closer_asignado": bool(closer_id),
        "auto_analisis": tiene_transcript,
    }
