"""Upsert idempotente de perfiles en Supabase (dedup por username).

Re-buscar el mismo nicho no duplica: actualiza datos + score + scraped_at. Es el
mismo patrón que el import idempotente de Tokko (dedup por id de propiedad).
"""
from datetime import datetime, timezone

from .supabase_client import get_supabase_admin


def _existentes(sb, usernames: list[str]) -> set[str]:
    """Devuelve el subconjunto de usernames que ya están en la DB."""
    encontrados: set[str] = set()
    # Supabase limita el tamaño del in_(); vamos por lotes.
    for i in range(0, len(usernames), 200):
        lote = usernames[i:i + 200]
        res = sb.table("ig_profiles").select("username").in_("username", lote).execute()
        encontrados.update(r["username"] for r in (res.data or []))
    return encontrados


def upsert_perfiles(perfiles: list[dict], nicho_id: str | None, scores: dict[str, int]) -> tuple[int, int]:
    """Inserta/actualiza perfiles. Devuelve (total, nuevos).

    perfiles: lista de dicts ya normalizados (contrato de collector).
    scores:   {username: score_nicho}.
    """
    if not perfiles:
        return (0, 0)

    sb = get_supabase_admin()
    usernames = [p["username"] for p in perfiles]
    ya = _existentes(sb, usernames)
    nuevos = sum(1 for u in usernames if u not in ya)

    ahora = datetime.now(timezone.utc).isoformat()
    filas = []
    for p in perfiles:
        filas.append({
            **p,
            "nicho_id": nicho_id,
            "score_nicho": scores.get(p["username"], 0),
            "scraped_at": ahora,
        })

    # upsert por PK (username) en lotes.
    for i in range(0, len(filas), 200):
        sb.table("ig_profiles").upsert(filas[i:i + 200], on_conflict="username").execute()

    return (len(filas), nuevos)
