"""Router de Conexiones — cada usuario conecta SUS propias integraciones.

- Telegram (setters): generar/mostrar el código de vinculación de su propio chat.
- Fathom (closers): pegar su API key → se registra un webhook en Fathom que empuja
  sus llamadas directo a SALEMETRIQ, atribuidas a él por un token propio.

Todo self-service: opera sobre el usuario logueado (get_current_user), no requiere
admin. El admin mantiene su gestión aparte en /api/workspace.
"""
import secrets
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..services import fathom_api
from ..services.auth import get_current_user
from ..services.crypto import encrypt
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/conexiones", tags=["conexiones"])

_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _codigo_telegram() -> str:
    return "SMQ-" + "".join(secrets.choice(_ALFABETO) for _ in range(6))


class FathomConnect(BaseModel):
    api_key: str


# ── Estado de mis conexiones ─────────────────────────────────────────────────
@router.get("")
def estado(user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    row = (
        sb.table("users")
        .select("rol, telegram_user_id, telegram_link_code, fathom_connected_at")
        .eq("id", user["id"]).limit(1).execute().data
    )
    u = row[0] if row else {}
    return {
        "rol": u.get("rol"),
        "telegram": {
            "vinculado": u.get("telegram_user_id") is not None,
            "codigo": u.get("telegram_link_code"),
        },
        "fathom": {
            "conectado": u.get("fathom_connected_at") is not None,
            "conectado_at": u.get("fathom_connected_at"),
        },
    }


# ── Telegram (self-service) ──────────────────────────────────────────────────
@router.post("/telegram/code")
def generar_codigo_telegram(user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    for _ in range(5):
        code = _codigo_telegram()
        if not sb.table("users").select("id").eq("telegram_link_code", code).limit(1).execute().data:
            break
    # Generar un código nuevo desvincula el chat anterior (empezás de cero).
    sb.table("users").update(
        {"telegram_link_code": code, "telegram_user_id": None}
    ).eq("id", user["id"]).execute()
    return {"codigo": code}


@router.delete("/telegram")
def desvincular_telegram(user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    sb.table("users").update(
        {"telegram_user_id": None, "telegram_link_code": None}
    ).eq("id", user["id"]).execute()
    return {"ok": True}


# ── Fathom (self-service: pegar API key → auto-registrar webhook) ────────────
@router.post("/fathom")
def conectar_fathom(body: FathomConnect, user: dict = Depends(get_current_user)) -> dict:
    api_key = body.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="Pegá tu API key de Fathom")
    if not settings.PUBLIC_BACKEND_URL:
        raise HTTPException(
            status_code=503,
            detail="Falta configurar PUBLIC_BACKEND_URL en el backend para conectar Fathom.",
        )

    # 1) Validar la key
    try:
        if not fathom_api.validar_key(api_key):
            raise HTTPException(status_code=400, detail="API key de Fathom inválida.")
    except fathom_api.FathomError as e:
        raise HTTPException(status_code=502, detail=str(e))

    sb = get_supabase_admin()
    prev = (
        sb.table("users").select("fathom_user_token, fathom_webhook_id")
        .eq("id", user["id"]).limit(1).execute().data
    )
    prev = prev[0] if prev else {}

    # 2) Token propio del usuario (para la URL del webhook)
    user_token = prev.get("fathom_user_token") or secrets.token_hex(16)

    # 3) Si ya había un webhook, lo borramos para no duplicar
    if prev.get("fathom_webhook_id"):
        fathom_api.borrar_webhook(api_key, prev["fathom_webhook_id"])

    # 4) Registrar el webhook en Fathom
    destino = f"{settings.PUBLIC_BACKEND_URL.rstrip('/')}/api/fathom/webhook?token={user_token}"
    try:
        wh = fathom_api.crear_webhook(api_key, destino)
    except fathom_api.FathomError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 5) Guardar (API key cifrada)
    ahora = datetime.now(timezone.utc).isoformat()
    sb.table("users").update({
        "fathom_user_token": user_token,
        "fathom_api_key_enc": encrypt(api_key),
        "fathom_webhook_id": wh.get("id"),
        "fathom_webhook_secret": wh.get("secret"),
        "fathom_connected_at": ahora,
    }).eq("id", user["id"]).execute()

    return {"conectado": True, "conectado_at": ahora}


@router.delete("/fathom")
def desconectar_fathom(user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    from ..services.crypto import decrypt

    row = (
        sb.table("users").select("fathom_api_key_enc, fathom_webhook_id")
        .eq("id", user["id"]).limit(1).execute().data
    )
    u = row[0] if row else {}
    key_enc = u.get("fathom_api_key_enc")
    wh_id = u.get("fathom_webhook_id")
    if key_enc and wh_id:
        key = decrypt(key_enc)
        if key:
            fathom_api.borrar_webhook(key, wh_id)

    sb.table("users").update({
        "fathom_api_key_enc": None,
        "fathom_webhook_id": None,
        "fathom_webhook_secret": None,
        "fathom_connected_at": None,
    }).eq("id", user["id"]).execute()
    return {"ok": True}
