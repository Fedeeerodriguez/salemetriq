"""Fuente de datos: Apify (actor apify/instagram-scraper).

Traduce cada ÁNGULO al input correcto del actor y siempre devuelve PERFILES
completos (no posts, metadata ni comentarios). Cada ángulo segmenta distinto:

  - keyword    → búsqueda de usuarios (searchType=user, resultsType=details) → perfiles directos.
  - hashtag    → posts del tag (directUrl + resultsType=posts) → ownerUsername → enrich a perfil.
  - ubicacion  → place search → location_id/slug → posts de la ubicación → ownerUsername → enrich.
  - followers  → "audiencia" de la cuenta semilla: comentaristas de sus posts recientes → enrich.
                 (Instagram no deja listar followers sin login; los que comentan son audiencia
                  engaged real del nicho, la mejor aproximación con el actor free.)

Sin APIFY_TOKEN → MODO MOCK (perfiles de ejemplo deterministas) para dev sin gastar crédito.
"""
import hashlib
import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(300.0, connect=15.0)
_POSTS_AUDIENCIA = 8   # posts de la semilla a escanear para sacar comentaristas


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
    usernames = [u for u in usernames if u][:limite]
    if not usernames:
        return []
    urls = [f"https://www.instagram.com/{u}/" for u in usernames]
    out: list[dict[str, Any]] = []
    for i in range(0, len(urls), 50):
        out += _run({"directUrls": urls[i:i + 50], "resultsType": "details"})
    # Filtrar items de error (perfiles privados/inexistentes vienen con 'error').
    return [p for p in out if not p.get("error")]


def _unicos(valores) -> list[str]:
    """Únicos preservando orden, sin vacíos."""
    return [v for v in dict.fromkeys(x for x in valores if x)]


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
            owners = _unicos(p.get("ownerUsername") for p in posts)
            return _enrich(owners, limite)

        if angulo == "ubicacion":
            return _buscar_ubicacion(q, limite)

        if angulo == "followers":
            return _buscar_audiencia(q, limite)

        return _run({"search": q, "searchType": "user", "resultsType": "details", "resultsLimit": limite})

    except httpx.HTTPError as e:
        logger.error("Apify falló (%s %s): %s", angulo, query, e)
        raise RuntimeError(f"Error consultando Apify: {e}") from e


def _buscar_ubicacion(q: str, limite: int) -> list[dict[str, Any]]:
    """place search → URL de la ubicación → posts → dueños → perfil completo."""
    lugares = _run({"search": q, "searchType": "place", "resultsType": "details", "searchLimit": 3})
    for lugar in lugares:
        lid, slug = lugar.get("location_id"), lugar.get("slug")
        if not lid:
            continue
        loc_url = f"https://www.instagram.com/explore/locations/{lid}/{slug or 'x'}/"
        posts = _run({"directUrls": [loc_url], "resultsType": "posts", "resultsLimit": limite})
        owners = _unicos(p.get("ownerUsername") for p in posts)
        if owners:
            return _enrich(owners, limite)
    # Fallback: si no se encontró la ubicación, buscar usuarios con el término.
    logger.info("Ubicación '%s' sin posts; fallback a búsqueda de usuarios.", q)
    return _run({"search": q, "searchType": "user", "resultsType": "details",
                 "resultsLimit": limite, "searchLimit": limite})


def _buscar_audiencia(cuenta: str, limite: int) -> list[dict[str, Any]]:
    """Comentaristas de los posts recientes de la cuenta semilla → perfil completo.

    Aproxima "seguidores" por audiencia ENGAGED (los que comentan), que es lo mejor
    que se puede segmentar sin login. Excluye a la propia cuenta semilla.
    """
    posts = _run({"directUrls": [f"https://www.instagram.com/{cuenta}/"],
                  "resultsType": "posts", "resultsLimit": _POSTS_AUDIENCIA})
    shortcodes = _unicos(p.get("shortCode") for p in posts)
    if not shortcodes:
        logger.info("Audiencia @%s: la cuenta no tiene posts accesibles.", cuenta)
        return []
    post_urls = [f"https://www.instagram.com/p/{s}/" for s in shortcodes]
    comentarios = _run({"directUrls": post_urls, "resultsType": "comments",
                        "resultsLimit": max(limite * 3, 30)})
    commenters = [u for u in _unicos(c.get("ownerUsername") for c in comentarios) if u.lower() != cuenta.lower()]
    return _enrich(commenters, limite)


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
