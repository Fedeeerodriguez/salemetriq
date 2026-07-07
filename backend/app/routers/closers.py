"""Router de closers — listado y detalle con métricas de llamadas.

En Fase 0 devuelve lo que haya en Supabase. La lógica de scoring IA sobre los
transcripts se agrega en la Fase 3.
"""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/closers", tags=["closers"])


@router.get("")
def listar_closers(user: dict = Depends(get_current_user)) -> list[dict]:
    """Closers con métricas agregadas de sus llamadas (para el ranking)."""
    sb = get_supabase_admin()
    demo = bool(user.get("is_demo"))
    closers = (
        sb.table("users").select("id, nombre, email, rol")
        .eq("rol", "closer").eq("is_demo", demo).execute().data or []
    )
    if not closers:
        return []

    ids = [c["id"] for c in closers]
    calls = (
        sb.table("calls").select("closer_id, outcome, deal_value")
        .in_("closer_id", ids).eq("is_demo", demo).execute().data or []
    )
    agg: dict[str, dict] = {}
    for c in calls:
        a = agg.setdefault(c["closer_id"], {"llamadas": 0, "cerradas": 0, "revenue": 0.0})
        a["llamadas"] += 1
        if c.get("outcome") == "cerro":
            a["cerradas"] += 1
            a["revenue"] += float(c.get("deal_value") or 0)

    for c in closers:
        a = agg.get(c["id"], {"llamadas": 0, "cerradas": 0, "revenue": 0.0})
        c["llamadas"] = a["llamadas"]
        c["cerradas"] = a["cerradas"]
        c["revenue"] = round(a["revenue"], 2)
        c["close_rate"] = round(a["cerradas"] / a["llamadas"] * 100, 1) if a["llamadas"] else 0.0

    closers.sort(key=lambda x: (x["close_rate"], x["revenue"]), reverse=True)
    return closers


@router.get("/{closer_id}/llamadas")
def llamadas_de_closer(closer_id: str, user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = (
        sb.table("calls")
        .select("id, fecha, duracion_seg, outcome, deal_value, transcript")
        .eq("closer_id", closer_id)
        .eq("is_demo", bool(user.get("is_demo")))
        .order("fecha", desc=True)
        .execute()
    )
    return res.data or []
