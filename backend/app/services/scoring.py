"""Scoring de afinidad al nicho (0..100).

Heurística barata (sin IA) que puntúa qué tan probable es que un perfil sea del
nicho buscado. La IA (Fase 4) es un refinamiento opcional encima de esto.

Señales:
  - keywords del nicho presentes en bio / full_name / category  (peso alto)
  - la query de la búsqueda aparece en el texto                  (peso medio)
  - es cuenta profesional / business                             (peso bajo)
  - tiene email o web público (señal de cuenta "real"/contactable) (peso bajo)
"""
import re


def _texto(perfil: dict) -> str:
    partes = [perfil.get("bio"), perfil.get("full_name"), perfil.get("category")]
    return " ".join(p for p in partes if p).lower()


def _contiene(texto: str, termino: str) -> bool:
    t = termino.strip().lower()
    if not t:
        return False
    # match por palabra completa cuando es una sola palabra; substring si es frase.
    if " " in t:
        return t in texto
    return re.search(rf"\b{re.escape(t)}\b", texto) is not None


def score(perfil: dict, nicho: dict | None, query: str = "") -> int:
    texto = _texto(perfil)
    puntos = 0

    keywords = (nicho or {}).get("keywords") or []
    if keywords:
        hits = sum(1 for k in keywords if _contiene(texto, k))
        # hasta 60 pts por coincidencias de keywords (satura a los 3 hits).
        puntos += min(hits, 3) * 20

    if query and _contiene(texto, query.lstrip("@#")):
        puntos += 20

    if perfil.get("is_business"):
        puntos += 10

    if perfil.get("email_publico") or perfil.get("external_url"):
        puntos += 10

    return max(0, min(100, puntos))
