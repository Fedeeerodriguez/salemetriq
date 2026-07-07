"""Herramienta de arranque del bot de Telegram (Fase A).

Dos usos:

  # Polling — para PROBAR EN LOCAL sin URL pública. Lee mensajes con getUpdates
  # y los procesa con el mismo código que el webhook. Cortá con Ctrl+C.
  .venv/Scripts/python scripts/telegram_bot.py poll

  # Webhook — para PRODUCCIÓN. Registra la URL pública del backend en Telegram.
  .venv/Scripts/python scripts/telegram_bot.py set-webhook https://TU-BACKEND/api/telegram/webhook

  # Borra el webhook (necesario antes de usar poll si ya registraste uno).
  .venv/Scripts/python scripts/telegram_bot.py delete-webhook

Requiere TELEGRAM_BOT_TOKEN en backend/.env.
"""
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.routers.telegram import procesar_update  # noqa: E402
from app.services import telegram as tg  # noqa: E402

API = "https://api.telegram.org"


def _base() -> str:
    if not settings.TELEGRAM_BOT_TOKEN:
        print("ERROR: falta TELEGRAM_BOT_TOKEN en backend/.env")
        sys.exit(1)
    return f"{API}/bot{settings.TELEGRAM_BOT_TOKEN}"


def poll() -> None:
    print("[poll] Escuchando mensajes… (Ctrl+C para cortar)")
    offset = None
    with httpx.Client(timeout=40) as c:
        while True:
            try:
                params = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset
                r = c.get(f"{_base()}/getUpdates", params=params).json()
                for upd in r.get("result", []):
                    offset = upd["update_id"] + 1
                    who = (upd.get("message") or {}).get("from", {}).get("id")
                    print(f"[poll] update {upd['update_id']} de {who}")
                    try:
                        procesar_update(upd)
                    except Exception as e:  # noqa: BLE001
                        print(f"[poll] error procesando: {e}")
            except KeyboardInterrupt:
                print("\n[poll] cortado.")
                return
            except Exception as e:  # noqa: BLE001
                print(f"[poll] error de red: {e}; reintento en 3s")
                time.sleep(3)


def set_webhook(url: str) -> None:
    print(f"[set-webhook] {url}")
    print(tg.set_webhook(url))


def delete_webhook() -> None:
    with httpx.Client(timeout=15) as c:
        print(c.post(f"{_base()}/deleteWebhook").json())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "poll"
    if cmd == "poll":
        poll()
    elif cmd == "set-webhook":
        if len(sys.argv) < 3:
            print("Uso: telegram_bot.py set-webhook https://TU-BACKEND/api/telegram/webhook")
            sys.exit(1)
        set_webhook(sys.argv[2])
    elif cmd == "delete-webhook":
        delete_webhook()
    else:
        print(__doc__)
