"""Fuente de datos: Apify (plan free — no usa tu cuenta de IG, cero riesgo de ban).

Llama al actor de Instagram de Apify vía la API run-sync-get-dataset-items y
devuelve los items crudos. `collector.normalizar()` los lleva al contrato común.

Sin APIFY_TOKEN configurado, cae a un MODO MOCK que devuelve perfiles de ejemplo
deterministas — así el flujo completo (buscar → puntuar → listar → exportar) se
puede probar en dev sin gastar crédito.
"""
import hashlib
import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# Cuánto esperamos al actor (scraping real puede tardar bastante).
_TIMEOUT = httpx.Timeout(180.0, connect=15.0)


def _apify_input(angulo: str, query: str, limite: int) -> dict[str, Any]:
    """Traduce nuestro ángulo al input del actor apify/instagram-scraper."""
    q = query.strip().lstrip("@#")
    if angulo == "hashtag":
        return {"search": q, "searchType": "hashtag", "resultsType": "details",
                "resultsLimit": limite, "searchLimit": 1}
    if angulo == "keyword":
        return {"search": q, "searchType": "user", "resultsType": "details",
                "resultsLimit": limite, "searchLimit": limite}
    if angulo == "followers":
        # Seguidores de una cuenta semilla.
        return {"directUrls": [f"https://www.instagram.com/{q}/"],
                "resultsType": "followers", "resultsLimit": limite}
    if angulo == "ubicacion":
        return {"search": q, "searchType": "place", "resultsType": "details",
                "resultsLimit": limite, "searchLimit": 1}
    return {"search": q, "searchType": "user", "resultsType": "details", "resultsLimit": limite}


def buscar(angulo: str, query: str, filtros: dict) -> list[dict[str, Any]]:
    limite = min(int(filtros.get("limite") or settings.APIFY_MAX_RESULTS), settings.APIFY_MAX_RESULTS)

    if not settings.APIFY_TOKEN:
        logger.warning("APIFY_TOKEN no configurado — usando MODO MOCK (%s perfiles de ejemplo).", limite)
        return _mock(angulo, query, min(limite, 12))

    actor = settings.APIFY_ACTOR.replace("/", "~")  # la API usea ~ como separador
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                url,
                params={"token": settings.APIFY_TOKEN},
                json=_apify_input(angulo, query, limite),
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("items", [])
    except httpx.HTTPError as e:
        logger.error("Apify falló (%s %s): %s", angulo, query, e)
        raise RuntimeError(f"Error consultando Apify: {e}") from e


# ── Modo mock (dev sin token) ────────────────────────────────────────────────
def _mock(angulo: str, query: str, n: int) -> list[dict[str, Any]]:
    """Perfiles de ejemplo deterministas basados en la query (para dev/demo)."""
    base = query.strip().lstrip("@#").lower() or "perfil"
    out: list[dict[str, Any]] = []
    for i in range(n):
        seed = int(hashlib.sha256(f"{base}{i}".encode()).hexdigest(), 16)
        followers = 500 + (seed % 90000)
        tiene_negocio = (seed % 3) == 0
        out.append({
            "username": f"{base}_{i+1}",
            "fullName": f"{base.capitalize()} Demo {i+1}",
            "biography": f"{base} · ejemplo #{i+1} · info y turnos",
            "followersCount": followers,
            "followsCount": 100 + (seed % 2000),
            "postsCount": seed % 800,
            "isBusinessAccount": tiene_negocio,
            "businessCategoryName": base if tiene_negocio else None,
            "externalUrl": f"https://{base}{i+1}.com" if tiene_negocio else None,
            "businessEmail": f"contacto@{base}{i+1}.com" if tiene_negocio else None,
        })
    return out
