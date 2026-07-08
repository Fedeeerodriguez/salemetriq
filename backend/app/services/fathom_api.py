"""Cliente de la API pública de Fathom (developers.fathom.ai).

Se usa para conectar la cuenta de un usuario: validar su API key y registrar un
webhook que empuje sus llamadas a SALEMETRIQ. Auth: `Authorization: Bearer <key>`.
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

BASE = "https://api.fathom.ai/external/v1"

# Tipos de grabación que disparan el webhook (las propias del closer + las
# compartidas con externos, que es lo típico de una llamada de ventas).
TRIGGERED_FOR = ["my_recordings", "shared_external_recordings"]


class FathomError(Exception):
    """Error al hablar con la API de Fathom (con mensaje apto para el usuario)."""


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def validar_key(api_key: str) -> bool:
    """Devuelve True si la API key es válida (llamada liviana a /team_members)."""
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get(f"{BASE}/team_members", headers=_headers(api_key), params={"limit": 1})
        if r.status_code == 200:
            return True
        if r.status_code in (401, 403):
            return False
        raise FathomError(f"Fathom respondió {r.status_code} al validar la key.")
    except httpx.HTTPError as e:
        raise FathomError(f"No se pudo contactar a Fathom: {e}") from e


def crear_webhook(api_key: str, destination_url: str) -> dict:
    """Registra un webhook en Fathom. Devuelve {id, secret} de la respuesta."""
    payload = {
        "destination_url": destination_url,
        "triggered_for": TRIGGERED_FOR,
        "include_transcript": True,
        "include_summary": True,
    }
    try:
        with httpx.Client(timeout=20) as c:
            r = c.post(f"{BASE}/webhooks", headers=_headers(api_key), json=payload)
    except httpx.HTTPError as e:
        raise FathomError(f"No se pudo contactar a Fathom: {e}") from e
    if r.status_code not in (200, 201):
        logger.warning("Fathom crear_webhook %s: %s", r.status_code, r.text[:300])
        raise FathomError(f"Fathom rechazó el registro del webhook ({r.status_code}).")
    data = r.json()
    return {"id": data.get("id"), "secret": data.get("secret")}


def borrar_webhook(api_key: str, webhook_id: str) -> None:
    """Elimina el webhook en Fathom (al desconectar). No lanza si ya no existe."""
    try:
        with httpx.Client(timeout=15) as c:
            r = c.delete(f"{BASE}/webhooks/{webhook_id}", headers=_headers(api_key))
        if r.status_code not in (200, 204, 404):
            logger.warning("Fathom borrar_webhook %s: %s", r.status_code, r.text[:200])
    except httpx.HTTPError:
        logger.exception("Fallo borrando webhook de Fathom")
