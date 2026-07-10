"""Collector — interfaz común de fuentes de datos de Instagram.

Diseño enchufable: hoy la implementación es Apify (seguro, no arriesga tu cuenta).
Mañana se puede sumar otra fuente (login+Playwright, instaloader) sin tocar el
resto de la app: alcanza con exponer `buscar(angulo, query, filtros)`.

Devuelve perfiles NORMALIZADOS (siempre las mismas claves) para que scoring,
dedup y la UI no dependan del proveedor.
"""
from typing import Any

from . import collector_apify

# Claves canónicas de un perfil (contrato que ve el resto del sistema).
CAMPOS = (
    "username", "full_name", "bio", "followers", "following", "posts",
    "is_business", "category", "external_url", "email_publico",
    "telefono_publico", "profile_pic_url", "ig_url",
)


def normalizar(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Lleva un registro crudo del proveedor al contrato canónico."""
    username = (raw.get("username") or raw.get("ownerUsername") or "").strip().lstrip("@").lower()
    if not username:
        return None
    return {
        "username": username,
        "full_name": raw.get("full_name") or raw.get("fullName"),
        "bio": raw.get("bio") or raw.get("biography"),
        "followers": _int(raw.get("followers") or raw.get("followersCount")),
        "following": _int(raw.get("following") or raw.get("followsCount")),
        "posts": _int(raw.get("posts") or raw.get("postsCount")),
        "is_business": raw.get("is_business") if raw.get("is_business") is not None else raw.get("isBusinessAccount"),
        "category": raw.get("category") or raw.get("businessCategoryName"),
        "external_url": raw.get("external_url") or raw.get("externalUrl"),
        "email_publico": raw.get("email_publico") or raw.get("publicEmail") or raw.get("businessEmail"),
        "telefono_publico": raw.get("telefono_publico") or raw.get("publicPhoneNumber") or raw.get("businessPhoneNumber"),
        "profile_pic_url": raw.get("profile_pic_url") or raw.get("profilePicUrl"),
        "ig_url": raw.get("ig_url") or f"https://www.instagram.com/{username}/",
    }


def _int(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def buscar(angulo: str, query: str, filtros: dict | None = None) -> list[dict[str, Any]]:
    """Punto de entrada único. Delega en el proveedor y normaliza la salida.

    angulo: 'hashtag' | 'keyword' | 'followers' | 'ubicacion'
    query:  el hashtag (sin #), la palabra clave, el @usuario o la ubicación.
    """
    filtros = filtros or {}
    crudos = collector_apify.buscar(angulo, query, filtros)
    perfiles = [p for p in (normalizar(r) for r in crudos) if p]
    # Dedup dentro del mismo batch por username.
    vistos: dict[str, dict] = {}
    for p in perfiles:
        vistos[p["username"]] = p
    return list(vistos.values())
