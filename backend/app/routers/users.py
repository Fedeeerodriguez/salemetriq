"""Router de perfil de usuario — ficha densa con KPIs, dimensiones y timeline.

`GET /api/users/{id}/profile` arma la vista de un closer o un setter:
- closer → métricas de llamadas, score IA promedio, dimensiones, sentiment, timeline
- setter → set rate, calidad de leads, timeline de resúmenes
Respeta el aislamiento demo (solo cruza filas con el mismo is_demo del usuario).
"""
from fastapi import APIRouter, Depends, HTTPException

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/users", tags=["users"])

DIMS = ["apertura", "descubrimiento", "pitch", "objeciones", "cierre"]


def _lead_names(sb, lead_ids: list[str]) -> dict:
    if not lead_ids:
        return {}
    rows = sb.table("leads").select("id, nombre").in_("id", lead_ids).execute().data or []
    return {r["id"]: r["nombre"] for r in rows}


@router.get("/{user_id}/profile")
def profile(user_id: str, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    demo = bool(user.get("is_demo"))

    u = (
        sb.table("users").select("id, nombre, email, rol")
        .eq("id", user_id).eq("is_demo", demo).limit(1).execute().data
    )
    u = u[0] if u else None
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    base = {"id": u["id"], "nombre": u["nombre"], "email": u["email"], "rol": u["rol"]}

    # ── Closer ────────────────────────────────────────────────────────────────
    if u["rol"] == "closer":
        calls = (
            sb.table("calls").select("id, fecha, outcome, deal_value, lead_id")
            .eq("closer_id", user_id).eq("is_demo", demo).order("fecha", desc=True).execute().data or []
        )
        total = len(calls)
        cerradas = sum(1 for c in calls if c.get("outcome") == "cerro")
        revenue = round(sum((c.get("deal_value") or 0) for c in calls), 2)
        close_rate = round(cerradas / total * 100, 1) if total else 0.0

        ids = [c["id"] for c in calls]
        runs = (
            sb.table("analysis_runs").select("score, sentiment, raw")
            .eq("target_tipo", "call").in_("target_id", ids).execute().data or []
        ) if ids else []
        scores = [r["score"] for r in runs if r.get("score") is not None]
        score_prom = round(sum(scores) / len(scores), 1) if scores else None

        dim_acc = {d: [] for d in DIMS}
        sentiment = {"positivo": 0, "neutral": 0, "negativo": 0}
        for r in runs:
            d = (r.get("raw") or {}).get("dimensiones") or {}
            for k in DIMS:
                if k in d:
                    dim_acc[k].append(d[k])
            if r.get("sentiment") in sentiment:
                sentiment[r["sentiment"]] += 1
        dimensiones = [
            {"k": k, "v": round(sum(v) / len(v)) if v else 0} for k, v in dim_acc.items()
        ]

        leads = _lead_names(sb, list({c["lead_id"] for c in calls if c.get("lead_id")}))
        timeline = [
            {
                "fecha": c["fecha"],
                "titulo": leads.get(c.get("lead_id")) or "Lead",
                "outcome": c.get("outcome"),
                "valor": c.get("deal_value") or 0,
            }
            for c in calls[:12]
        ]

        base.update({
            "kpis": [
                {"label": "Close rate", "value": f"{close_rate}%"},
                {"label": "Facturación", "value": revenue, "money": True, "premium": True},
                {"label": "Llamadas", "value": total},
                {"label": "Score prom", "value": score_prom if score_prom is not None else "—"},
            ],
            "dimensiones": dimensiones,
            "sentiment": sentiment,
            "timeline": timeline,
        })

    # ── Setter ────────────────────────────────────────────────────────────────
    elif u["rol"] == "setter":
        summ = (
            sb.table("setter_summaries")
            .select("id, fecha, tipo, texto, lead_qualification, agendado, lead_id")
            .eq("setter_id", user_id).eq("is_demo", demo).order("fecha", desc=True).execute().data or []
        )
        total = len(summ)
        agendados = sum(1 for s in summ if s.get("agendado"))
        set_rate = round(agendados / total * 100, 1) if total else 0.0

        calif: dict[str, int] = {}
        for s in summ:
            q = s.get("lead_qualification") or "Sin calificar"
            calif[q] = calif.get(q, 0) + 1

        leads = _lead_names(sb, list({s["lead_id"] for s in summ if s.get("lead_id")}))
        timeline = [
            {
                "fecha": s["fecha"],
                "titulo": leads.get(s.get("lead_id")) or "Lead",
                "tipo": s.get("tipo"),
                "agendado": s.get("agendado"),
                "calif": s.get("lead_qualification"),
                "texto": s.get("texto"),
            }
            for s in summ[:12]
        ]

        base.update({
            "kpis": [
                {"label": "Set rate", "value": f"{set_rate}%"},
                {"label": "Reuniones agendadas", "value": agendados},
                {"label": "Resúmenes", "value": total},
            ],
            "calificaciones": [{"k": k, "v": v} for k, v in sorted(calif.items(), key=lambda x: -x[1])],
            "timeline": timeline,
        })

    else:
        base.update({"kpis": [], "timeline": []})

    return base
