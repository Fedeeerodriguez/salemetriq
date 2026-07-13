"""Fuente de datos: Apify (actor apify/instagram-scraper).

Traduce cada ÁNGULO al input correcto del actor y siempre devuelve PERFILES
(no posts ni metadata):

  - keyword    → búsqueda de usuarios (searchType=user, resultsType=details) → perfiles directos.
  - hashtag    → posts del tag (directUrl + resultsType=posts) → ownerUsername → enrich a perfil.
  - ubicacion  → búsqueda de lugar → posts → ownerUsername → enrich a perfil.
  - followers  → perfil de la cuenta semilla (el actor free no lista followers de forma fiable).

Sin APIFY_TOKEN → MODO MOCK (perfiles de ejemplo deterministas) para dev sin gastar crédito.
"""
import hashlib
import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(300.0, connect=15.0)


def _run(inp: dict[str, Any]) -> list[dict[str, Any]]:
    """Corre el actor (run-sync) y devuelve los items crudos del dataset."""
    actor = settings.APIFY_ACTOR.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(url, params={"token": settings.APIFY_TOKEN}, json=inp)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("items", [])


def _enrich(usernames: list[str], limite: int) -> list[dict[str, Any]]:
    """Trae el perfil COMPLETO (bio, followers, business…) de una lista de usuarios."""
    usernames = usernames[:limite]
    if not usernames:
        return []
    urls = [f"https://www.instagram.com/{u}/" for u in usernames]
    out: list[dict[str, Any]] = []
    for i in range(0, len(urls), 50):
        out += _run({"directUrls": urls[i:i + 50], "resultsType": "details"})
    return out


def _owners(posts: list[dict[str, Any]], limite: int) -> list[str]:
    """Usernames únicos dueños de una lista de posts (preserva orden)."""
    vistos = dict.fromkeys(p.get("ownerUsername") for p in posts if p.get("ownerUsername"))
    return list(vistos)[:limite]


def buscar(angulo: str, query: str, filtros: dict) -> list[dict[str, Any]]:
    limite = min(int(filtros.get("limite") or settings.APIFY_MAX_RESULTS), settings.APIFY_MAX_RESULTS)

    if not settings.APIFY_TOKEN:
        logger.warning("APIFY_TOKEN no configurado — usando MODO MOCK (%s perfiles de ejemplo).", limite)
        return _mock(angulo, query, min(limite, 12))

    q = query.strip().lstrip("@#")
    try:
        if angulo == "keyword":
            return _run({"search": q, "searchType": "user", "resultsType": "details",
                         "resultsLimit": limite, "searchLimit": limite})

        if angulo == "hashtag":
            posts = _run({"directUrls": [f"https://www.instagram.com/explore/tags/{q}/"],
                          "resultsType": "posts", "resultsLimit": limite})
            return _enrich(_owners(posts, limite), limite)

        if angulo == "ubicacion":
            # Buscar el lugar y traer posts de su página; de ahí, los dueños.
            posts = _run({"search": q, "searchType": "place", "resultsType": "posts",
                          "resultsLimit": limite, "searchLimit": 1})
            owners = _owners(posts, limite)
            if owners:
                return _enrich(owners, limite)
            # Fallback: búsqueda de usuarios con el término de ubicación.
            return _run({"search": q, "searchType": "user", "resultsType": "details",
                         "resultsLimit": limite, "searchLimit": limite})

        if angulo == "followers":
            # El actor free no lista followers de forma fiable → traemos el perfil de la semilla.
            logger.info("Ángulo 'followers': el actor free trae solo el perfil semilla @%s.", q)
            return _run({"directUrls": [f"https://www.instagram.com/{q}/"], "resultsType": "details"})

        return _run({"search": q, "searchType": "user", "resultsType": "details", "resultsLimit": limite})

    except httpx.HTTPError as e:
        logger.error("Apify falló (%s %s): %s", angulo, query, e)
        raise RuntimeError(f"Error consultando Apify: {e}") from e


# ── Modo mock (dev sin token) ────────────────────────────────────────────────
def _mock(angulo: str, query: str, n: int) -> list[dict[str, Any]]:
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
