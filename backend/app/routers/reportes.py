"""Router de reportes y alertas — capa de valor sobre los datos del workspace.

- GET /api/reportes/semanal  → KPIs de los últimos 7 días.
- GET /api/reportes/alertas  → señales accionables (lead caliente sin agendar,
  closer con score bajo, grabaciones sin analizar).
- GET /api/reportes/export.csv → export de llamadas del workspace.

Todo está scopeado por team_id del usuario logueado (multi-tenant).
"""
import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/reportes", tags=["reportes"])

SCORE_BAJO = 40  # umbral de alerta para closers


def _cutoff(dias: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


def _nombres(sb, user_ids: list[str]) -> dict[str, str]:
    ids = [i for i in set(user_ids) if i]
    if not ids:
        return {}
    rows = sb.table("users").select("id, nombre, email").in_("id", ids).execute().data or []
    return {r["id"]: (r.get("nombre") or r.get("email")) for r in rows}


@router.get("/semanal")
def reporte_semanal(user: dict = Depends(get_current_user)) -> dict:
    team = user.get("team_id")
    if not team:
        return {"vacio": True}
    sb = get_supabase_admin()
    desde = _cutoff(7)

    calls = (
        sb.table("calls").select("closer_id, outcome, deal_value, fecha")
        .eq("team_id", team).gte("fecha", desde).execute().data or []
    )
    summ = (
        sb.table("setter_summaries").select("setter_id, agendado, lead_qualification, fecha")
        .eq("team_id", team).gte("fecha", desde).execute().data or []
    )
    runs = (
        sb.table("analysis_runs").select("score, target_tipo, created_at")
        .eq("team_id", team).eq("target_tipo", "call_recording").gte("created_at", desde).execute().data or []
    )

    total_calls = len(calls)
    cerradas = sum(1 for c in calls if c.get("outcome") == "cerro")
    facturado = sum(c.get("deal_value") or 0 for c in calls if c.get("outcome") == "cerro")
    close_rate = round(cerradas / total_calls * 100) if total_calls else 0

    total_summ = len(summ)
    agendados = sum(1 for s in summ if s.get("agendado"))
    set_rate = round(agendados / total_summ * 100) if total_summ else 0

    scores = [r["score"] for r in runs if r.get("score") is not None]
    score_prom = round(sum(scores) / len(scores)) if scores else None

    # Ranking de closers por close rate (mínimo 1 llamada).
    porc: dict[str, dict] = {}
    for c in calls:
        a = porc.setdefault(c["closer_id"], {"n": 0, "cerr": 0})
        a["n"] += 1
        if c.get("outcome") == "cerro":
            a["cerr"] += 1
    nombres = _nombres(sb, list(porc.keys()))
    ranking = sorted(
        ({"closer_id": cid, "nombre": nombres.get(cid, "—"), "llamadas": a["n"],
          "cerradas": a["cerr"], "close_rate": round(a["cerr"] / a["n"] * 100) if a["n"] else 0}
         for cid, a in porc.items()),
        key=lambda x: (x["close_rate"], x["llamadas"]), reverse=True,
    )

    return {
        "periodo": {"dias": 7, "desde": desde},
        "llamadas": {"total": total_calls, "cerradas": cerradas, "close_rate": close_rate, "facturado": facturado},
        "setting": {"resumenes": total_summ, "agendados": agendados, "set_rate": set_rate},
        "calidad": {"analizadas": len(runs), "score_prom": score_prom},
        "ranking_closers": ranking,
    }


@router.get("/alertas")
def alertas(user: dict = Depends(get_current_user)) -> list[dict]:
    team = user.get("team_id")
    if not team:
        return []
    sb = get_supabase_admin()
    out: list[dict] = []

    # 1) Leads calientes sin agendar (últimos 14 días).
    calientes = (
        sb.table("setter_summaries").select("id, setter_id, texto, fecha, lead_qualification, agendado")
        .eq("team_id", team).eq("lead_qualification", "caliente").eq("agendado", False)
        .gte("fecha", _cutoff(14)).order("fecha", desc=True).execute().data or []
    )
    setter_nom = _nombres(sb, [s["setter_id"] for s in calientes])
    for s in calientes[:20]:
        out.append({
            "tipo": "lead_caliente_sin_agendar",
            "severidad": "alta",
            "titulo": "Lead caliente sin agendar",
            "detalle": (s.get("texto") or "")[:140],
            "quien": setter_nom.get(s["setter_id"]),
            "fecha": s.get("fecha"),
        })

    # 2) Closers con score promedio bajo (últimos 30 días).
    runs = (
        sb.table("analysis_runs").select("score, target_id")
        .eq("team_id", team).eq("target_tipo", "call_recording").gte("created_at", _cutoff(30))
        .execute().data or []
    )
    rec_ids = [r["target_id"] for r in runs if r.get("score") is not None]
    recs = (
        sb.table("call_recordings").select("id, closer_id").in_("id", rec_ids).execute().data
        if rec_ids else []
    ) or []
    rec_closer = {r["id"]: r.get("closer_id") for r in recs}
    por_closer: dict[str, list] = {}
    for r in runs:
        cid = rec_closer.get(r["target_id"])
        if cid and r.get("score") is not None:
            por_closer.setdefault(cid, []).append(r["score"])
    nombres = _nombres(sb, list(por_closer.keys()))
    for cid, sc in por_closer.items():
        prom = sum(sc) / len(sc)
        if len(sc) >= 2 and prom < SCORE_BAJO:
            out.append({
                "tipo": "closer_score_bajo",
                "severidad": "media",
                "titulo": "Closer con score bajo",
                "detalle": f"Score promedio {round(prom)} en {len(sc)} llamadas analizadas.",
                "quien": nombres.get(cid),
                "closer_id": cid,
            })

    # 3) Grabaciones con transcript sin analizar.
    sin_analizar = (
        sb.table("call_recordings").select("id", count="exact")
        .eq("team_id", team).eq("status", "nuevo").not_.is_("transcript", "null")
        .execute()
    )
    n_sin = sin_analizar.count or 0
    if n_sin:
        out.append({
            "tipo": "grabaciones_sin_analizar",
            "severidad": "baja",
            "titulo": "Grabaciones sin analizar",
            "detalle": f"{n_sin} llamada(s) con transcript esperando análisis.",
        })

    orden = {"alta": 0, "media": 1, "baja": 2}
    out.sort(key=lambda a: orden.get(a["severidad"], 3))
    return out


@router.get("/export.csv")
def export_csv(user: dict = Depends(get_current_user)) -> Response:
    team = user.get("team_id")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["fecha", "closer", "outcome", "deal_value", "duracion_seg"])
    if team:
        sb = get_supabase_admin()
        calls = (
            sb.table("calls").select("fecha, closer_id, outcome, deal_value, duracion_seg")
            .eq("team_id", team).order("fecha", desc=True).limit(2000).execute().data or []
        )
        nombres = _nombres(sb, [c.get("closer_id") for c in calls])
        for c in calls:
            w.writerow([
                c.get("fecha", ""), nombres.get(c.get("closer_id"), ""),
                c.get("outcome", ""), c.get("deal_value", ""), c.get("duracion_seg", ""),
            ])
    csv_bytes = "﻿" + buf.getvalue()  # BOM para Excel
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="salemetriq_llamadas.csv"'},
    )
