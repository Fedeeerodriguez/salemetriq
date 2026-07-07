"""Router de Telegram — Fase A: los setters mandan su resumen de setting al bot.

Flujo:
  1. El admin genera un código de vinculación para un setter (endpoint en
     workspace.py). Se lo pasa por fuera (mail/WhatsApp).
  2. El setter abre el bot y envía `/link CODIGO`. Guardamos su telegram_user_id.
  3. Cada mensaje posterior (texto o nota de voz) se estructura con Claude y se
     guarda en setter_summaries con su setter_id + team_id (multi-tenant).

El webhook se protege con el secret que Telegram reenvía en el header
`X-Telegram-Bot-Api-Secret-Token` (si TELEGRAM_WEBHOOK_SECRET está configurado).

La lógica vive en `procesar_update()` para que el webhook y el script de polling
de desarrollo (scripts/telegram_poll.py) compartan el mismo camino.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from ..config import settings
from ..services import telegram as tg
from ..services.setter_ia import estructurar_resumen
from ..services.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

_AYUDA = (
    "👋 Soy el bot de <b>SALEMETRIQ</b>.\n\n"
    "Para vincular tu cuenta, pedile el código a tu administrador y enviá:\n"
    "<code>/link TU-CODIGO</code>\n\n"
    "Una vez vinculado, mandame por acá el resumen de cada setting (texto o nota "
    "de voz) y lo cargo en la plataforma."
)


def _buscar_por_telegram(sb, telegram_user_id: int) -> dict | None:
    res = (
        sb.table("users")
        .select("id, nombre, team_id, rol, activo")
        .eq("telegram_user_id", telegram_user_id)
        .limit(1)
        .execute()
        .data
    )
    return res[0] if res else None


def _vincular(sb, code: str, telegram_user_id: int) -> dict | None:
    """Vincula el código a este chat de Telegram. Devuelve el user o None."""
    code = code.strip().upper()
    if not code:
        return None
    target = (
        sb.table("users").select("id, nombre, rol, activo")
        .eq("telegram_link_code", code).limit(1).execute().data
    )
    if not target:
        return None
    u = target[0]
    # Consumimos el código y guardamos el chat. El índice único evita que dos
    # personas usen el mismo telegram_user_id.
    sb.table("users").update(
        {"telegram_user_id": telegram_user_id, "telegram_link_code": None}
    ).eq("id", u["id"]).execute()
    return u


def _guardar_resumen(sb, user: dict, texto: str) -> dict:
    """Estructura el texto con Claude y lo inserta en setter_summaries."""
    est = estructurar_resumen(texto)
    row = {
        "setter_id": user["id"],
        "team_id": user["team_id"],
        "tipo": "texto",
        "fuente": "telegram",
        "texto": est.get("resumen") or texto,
        "lead_qualification": est.get("lead_qualification"),
        "agendado": bool(est.get("agendado")),
    }
    row = {k: v for k, v in row.items() if v is not None}
    sb.table("setter_summaries").insert(row).execute()
    return est


def procesar_update(update: dict) -> None:
    """Procesa un update de Telegram (webhook o polling). Nunca lanza hacia afuera."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    from_user = msg.get("from", {})
    telegram_user_id = from_user.get("id")
    if telegram_user_id is None:
        return

    sb = get_supabase_admin()
    text = (msg.get("text") or "").strip()

    # ── Comandos ──────────────────────────────────────────────────────────────
    if text.startswith("/start") or text.lower() in {"/help", "/ayuda"}:
        tg.send_message(chat_id, _AYUDA)
        return

    if text.startswith("/link"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            tg.send_message(chat_id, "Enviá el código así: <code>/link TU-CODIGO</code>")
            return
        u = _vincular(sb, parts[1], telegram_user_id)
        if not u:
            tg.send_message(chat_id, "❌ Código inválido o ya usado. Pedile uno nuevo a tu admin.")
        elif not u.get("activo", True):
            tg.send_message(chat_id, "Tu usuario está desactivado. Hablá con tu admin.")
        else:
            tg.send_message(
                chat_id,
                f"✅ ¡Listo, {u.get('nombre') or ''}! Tu cuenta quedó vinculada.\n\n"
                "Mandame el resumen de cada setting (texto o nota de voz) y lo cargo.",
            )
        return

    # ── Mensaje normal: debe venir de un usuario ya vinculado ─────────────────
    user = _buscar_por_telegram(sb, telegram_user_id)
    if not user:
        tg.send_message(chat_id, _AYUDA)
        return
    if not user.get("activo", True):
        tg.send_message(chat_id, "Tu usuario está desactivado. Hablá con tu admin.")
        return

    # Nota de voz → transcribir (si hay Whisper); si no, pedir texto.
    voice = msg.get("voice") or msg.get("audio")
    if voice:
        text = _transcribir(voice.get("file_id"))
        if not text:
            tg.send_message(
                chat_id,
                "🎙️ Recibí tu audio pero no puedo transcribirlo todavía "
                "(falta configurar la transcripción). Mandámelo por texto y lo cargo.",
            )
            return

    if not text:
        tg.send_message(chat_id, "Mandame el resumen del setting por texto o nota de voz 🙂")
        return

    try:
        est = _guardar_resumen(sb, user, text)
    except Exception:  # noqa: BLE001
        logger.exception("Fallo guardando resumen de setting desde Telegram")
        tg.send_message(chat_id, "⚠️ Hubo un problema al procesar tu resumen. Probá de nuevo en un rato.")
        return

    cal = est.get("lead_qualification", "—")
    ag = "sí" if est.get("agendado") else "no"
    prox = est.get("proximo_paso")
    conf = f"✅ Resumen cargado.\n\n<b>Lead:</b> {cal}\n<b>Agendado:</b> {ag}"
    if prox:
        conf += f"\n<b>Próximo paso:</b> {prox}"
    tg.send_message(chat_id, conf)


def _transcribir(file_id: str | None) -> str:
    """Transcribe una nota de voz con Whisper (OpenAI) si hay API key; si no, ''."""
    if not file_id or not settings.OPENAI_API_KEY:
        return ""
    blob = tg.download_voice(file_id)
    if not blob:
        return ""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        res = client.audio.transcriptions.create(
            model="whisper-1",
            file=("voz.ogg", blob, "audio/ogg"),
        )
        return (res.text or "").strip()
    except Exception:  # noqa: BLE001
        logger.exception("Fallo transcribiendo audio con Whisper")
        return ""


@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if not tg.enabled():
        raise HTTPException(status_code=503, detail="Bot de Telegram no configurado")
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if expected and x_telegram_bot_api_secret_token != expected:
        raise HTTPException(status_code=401, detail="Secret inválido")
    update = await request.json()
    procesar_update(update)
    return {"ok": True}
