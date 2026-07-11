"""Clasificador de nicho con IA — ¿este perfil es del nicho? sí/no/dudoso.

Refina el scoring heurístico con Claude (modelo barato). Se activa por nicho
(campo `usa_ia`). Sin ANTHROPIC_API_KEY cae a un veredicto HEURÍSTICO.
"""
import json
import logging

from ..config import settings

logger = logging.getLogger(__name__)

VEREDICTOS = {"si", "no", "dudoso"}


def _prompt(perfil: dict, nicho: dict) -> str:
    nombre_nicho = nicho.get("nombre", "el nicho")
    keywords = ", ".join(nicho.get("keywords") or []) or "—"
    return (
        f"Nicho objetivo: \"{nombre_nicho}\". Palabras clave esperadas: {keywords}.\n\n"
        f"Perfil de Instagram:\n"
        f"- Usuario: @{perfil.get('username','')}\n"
        f"- Nombre: {perfil.get('full_name') or '—'}\n"
        f"- Bio: {perfil.get('bio') or '—'}\n"
        f"- Categoría: {perfil.get('category') or '—'}\n"
        f"- ¿Cuenta profesional?: {'sí' if perfil.get('is_business') else 'no'}\n\n"
        f"¿Este perfil pertenece al nicho \"{nombre_nicho}\"? Respondé SOLO un JSON: "
        f'{{"veredicto": "si|no|dudoso", "motivo": "máx 12 palabras"}}.'
    )


def clasificar(perfil: dict, nicho: dict) -> tuple[str, str] | None:
    """Devuelve (veredicto, motivo) o None si no se pudo clasificar."""
    if settings.ANTHROPIC_API_KEY:
        try:
            return _clasificar_claude(perfil, nicho)
        except Exception as e:  # noqa: BLE001
            logger.warning("Clasificador IA (Claude) falló, uso heurística: %s", e)

    return _heuristico(perfil, nicho)


def _clasificar_claude(perfil: dict, nicho: dict) -> tuple[str, str]:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=settings.IGP_CLASIFICADOR_MODEL,
        max_tokens=120,
        messages=[{"role": "user", "content": _prompt(perfil, nicho)}],
    )
    texto = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    ini, fin = texto.find("{"), texto.rfind("}")
    data = json.loads(texto[ini:fin + 1]) if ini >= 0 else {}
    veredicto = str(data.get("veredicto", "dudoso")).lower().strip()
    if veredicto not in VEREDICTOS:
        veredicto = "dudoso"
    motivo = str(data.get("motivo", ""))[:140]
    return (veredicto, motivo)


def _heuristico(perfil: dict, nicho: dict) -> tuple[str, str]:
    score = perfil.get("score_nicho", 0)
    if score >= 60:
        return ("si", "(heurística) fuerte coincidencia de keywords")
    if score >= 30:
        return ("dudoso", "(heurística) coincidencia parcial")
    return ("no", "(heurística) sin señales del nicho")
