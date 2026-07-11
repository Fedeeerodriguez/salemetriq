"""Scoring de afinidad al nicho (0..100).

Heurística barata (sin IA) que puntúa qué tan probable es que un perfil sea del
nicho buscado. La IA (clasificador) es un refinamiento opcional encima de esto.
"""
import re


def _texto(perfil: dict) -> str:
    partes = [perfil.get("bio"), perfil.get("full_name"), perfil.get("category")]
    return " ".join(p for p in partes if p).lower()


def _contiene(texto: str, termino: str) -> bool:
    t = termino.strip().lower()
    if not t:
        return False
    if " " in t:
        return t in texto
    return re.search(rf"\b{re.escape(t)}\b", texto) is not None


def score(perfil: dict, nicho: dict | None, query: str = "") -> int:
    texto = _texto(perfil)
    puntos = 0

    keywords = (nicho or {}).get("keywords") or []
    if keywords:
        hits = sum(1 for k in keywords if _contiene(texto, k))
        puntos += min(hits, 3) * 20

    if query and _contiene(texto, query.lstrip("@#")):
        puntos += 20

    if perfil.get("is_business"):
        puntos += 10

    if perfil.get("email_publico") or perfil.get("external_url"):
        puntos += 10

    return max(0, min(100, puntos))
