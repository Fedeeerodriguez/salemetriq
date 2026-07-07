"""Router de métricas — agregados para el dashboard.

Fase 0: overview simple calculado on-the-fly. En la Fase 3 esto se moverá a la
tabla `metrics_daily` (pre-agregado) y sumará el scoring IA.
"""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/metricas", tags=["metricas"])


@router.get("/overview")
def overview(user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    team = user.get("team_id")
    if not team:
        return {"close_rate": 0.0, "revenue": 0, "total_calls": 0, "cerradas": 0,
                "presentaron": 0, "set_rate": 0.0, "total_summaries": 0, "agendados": 0}

    calls = sb.table("calls").select("id, outcome, deal_value").eq("team_id", team).execute().data or []
    summaries = sb.table("setter_summaries").select("id, agendado").eq("team_id", team).execute().data or []

    total_calls = len(calls)
    cerradas = sum(1 for c in calls if c.get("outcome") == "cerro")
    presentaron = sum(1 for c in calls if c.get("outcome") != "no_show")
    close_rate = round(cerradas / total_calls * 100, 1) if total_calls else 0.0
    revenue = round(sum((c.get("deal_value") or 0) for c in calls), 2)

    total_summaries = len(summaries)
    agendados = sum(1 for s in summaries if s.get("agendado"))
    set_rate = round(agendados / total_summaries * 100, 1) if total_summaries else 0.0

    return {
        "close_rate": close_rate,
        "revenue": revenue,
        "total_calls": total_calls,
        "cerradas": cerradas,
        "presentaron": presentaron,
        "set_rate": set_rate,
        "total_summaries": total_summaries,
        "agendados": agendados,
    }
