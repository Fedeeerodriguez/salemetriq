"""Cliente mínimo de la Bot API de Telegram (envío de mensajes + descarga de audio).

Todo se hace con httpx directo — la Bot API es HTTP simple. El token del bot sale
de `TELEGRAM_BOT_TOKEN`. Si no está configurado, `enabled()` devuelve False y el
router de Telegram responde 503.
"""
from __future__ import annotations

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org"


def enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


def _base() -> str:
    return f"{_API}/bot{settings.TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: int | str, text: str) -> None:
    """Manda un mensaje de texto al chat. No lanza si falla — solo loguea."""
    if not enabled():
        return
    try:
        with httpx.Client(timeout=15) as c:
            r = c.post(
                f"{_base()}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
            if r.status_code != 200:
                logger.warning("Telegram sendMessage %s: %s", r.status_code, r.text[:200])
    except Exception:  # noqa: BLE001 — nunca romper el webhook por un envío fallido
        logger.exception("Fallo enviando mensaje a Telegram")


def download_voice(file_id: str) -> bytes | None:
    """Descarga un archivo (nota de voz) por su file_id. Devuelve los bytes o None."""
    if not enabled():
        return None
    try:
        with httpx.Client(timeout=30) as c:
            meta = c.get(f"{_base()}/getFile", params={"file_id": file_id}).json()
            if not meta.get("ok"):
                logger.warning("Telegram getFile falló: %s", meta)
                return None
            path = meta["result"]["file_path"]
            blob = c.get(f"{_API}/file/bot{settings.TELEGRAM_BOT_TOKEN}/{path}")
            blob.raise_for_status()
            return blob.content
    except Exception:  # noqa: BLE001
        logger.exception("Fallo descargando audio de Telegram")
        return None


def set_webhook(url: str) -> dict:
    """Registra el webhook del bot apuntando a `url`. Pasa el secret si está seteado."""
    payload: dict = {"url": url, "allowed_updates": ["message"]}
    if settings.TELEGRAM_WEBHOOK_SECRET:
        payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
    with httpx.Client(timeout=15) as c:
        return c.post(f"{_base()}/setWebhook", json=payload).json()
