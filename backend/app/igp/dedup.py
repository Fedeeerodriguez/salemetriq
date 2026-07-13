"""Upsert idempotente de perfiles en Supabase (schema igp, dedup por username)."""
from datetime import datetime, timezone

from ..services.supabase_client import get_supabase_igp


def _existentes(sb, usernames: list[str]) -> set[str]:
    encontrados: set[str] = set()
    for i in range(0, len(usernames), 200):
        lote = usernames[i:i + 200]
        res = sb.table("ig_profiles").select("username").in_("username", lote).execute()
        encontrados.update(r["username"] for r in (res.data or []))
    return encontrados


def upsert_perfiles(perfiles: list[dict], nicho_id: str | None, scores: dict[str, int]) -> tuple[int, int]:
    """Inserta/actualiza perfiles. Devuelve (total, nuevos)."""
    if not perfiles:
        return (0, 0)

    sb = get_supabase_igp()
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

    for i in range(0, len(filas), 200):
        sb.table("ig_profiles").upsert(filas[i:i + 200], on_conflict="username").execute()

    return (len(filas), nuevos)
