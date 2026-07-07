"""Router de llamadas — listado global para la pantalla Calls.

Devuelve las llamadas ordenadas por fecha con el nombre del closer y del lead
resueltos (join manual, PostgREST no hace joins arbitrarios sin FK expuestas).
"""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.get("")
def listar_calls(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    calls = (
        sb.table("calls")
        .select("id, fecha, duracion_seg, outcome, deal_value, closer_id, lead_id")
        .eq("is_demo", bool(user.get("is_demo")))
        .order("fecha", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    if not calls:
        return []

    closer_ids = list({c["closer_id"] for c in calls if c.get("closer_id")})
    lead_ids = list({c["lead_id"] for c in calls if c.get("lead_id")})
    closers = {
        u["id"]: u["nombre"]
        for u in (sb.table("users").select("id, nombre").in_("id", closer_ids).execute().data or [])
    } if closer_ids else {}
    leads = {
        l["id"]: l["nombre"]
        for l in (sb.table("leads").select("id, nombre").in_("id", lead_ids).execute().data or [])
    } if lead_ids else {}

    for c in calls:
        c["closer_nombre"] = closers.get(c.get("closer_id"))
        c["lead_nombre"] = leads.get(c.get("lead_id"))
    return calls
