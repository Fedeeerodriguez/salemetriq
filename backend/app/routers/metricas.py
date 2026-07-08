"""Router de métricas — agregados para el dashboard.

Fase 0: overview simple calculado on-the-fly. En la Fase 3 esto se moverá a la
tabla `metrics_daily` (pre-agregado) y sumará el scoring IA.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/metricas", tags=["metricas"])

# Etiquetas legibles de las etapas del método (para el foco de la semana).
ETAPA_LABEL = {
    "cualificacion": "Cualificación",
    "visualizacion": "Visualización",
    "consecuencia": "Consecuencia y miedo",
    "pitch": "Pitch de la oferta",
    "objeciones": "Manejo de objeciones",
    "cierre": "Cierre",
}


def _money(n) -> str:
    return "$" + f"{round(float(n or 0)):,}".replace(",", ".")


def _corto(nombre: str | None, email: str | None = None) -> str:
    """'Federico Rodríguez' → 'Federico R.'; cae al email si no hay nombre."""
    n = (nombre or "").strip()
    if not n:
        return (email or "Alguien").split("@")[0]
    partes = n.split()
    return f"{partes[0]} {partes[1][0]}." if len(partes) > 1 else partes[0]


def _parse_dt(iso) -> datetime | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except (ValueError, TypeError):
        return None


def _hace(dt: datetime | None) -> str:
    if not dt:
        return ""
    seg = (datetime.now(timezone.utc) - dt).total_seconds()
    if seg < 60:
        return "Recién"
    if seg < 3600:
        return f"Hace {int(seg // 60)} min"
    if seg < 86400:
        h = int(seg // 3600)
        return f"Hace {h} h"
    d = int(seg // 86400)
    return f"Hace {d} d" if d < 7 else dt.strftime("%d/%m")


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


@router.get("/foco")
def foco(user: dict = Depends(get_current_user)) -> dict:
    """Foco de la semana — análisis general del equipo contra el método.

    Reutiliza la agregación de coaching (sin llamar a la IA, es barato) para
    detectar la etapa más débil y la técnica menos aplicada.
    """
    team = user.get("team_id")
    vacio = {
        "disponible": False,
        "titulo": "Sin llamadas analizadas todavía",
        "texto": "Conectá Fathom en Conexiones. En cuanto entren y se analicen tus "
                 "llamadas, acá vas a ver en qué enfocar la semana.",
        "score": None,
        "n": 0,
    }
    if not team:
        return vacio

    # Import diferido para evitar cargar el analista IA salvo que haga falta.
    from .coaching import _agregar, _runs_de

    sb = get_supabase_admin()
    agg = _agregar(_runs_de(sb, team))
    n = agg.get("n") or 0
    if not n:
        return vacio

    etapa = agg.get("etapa_debil")
    titulo = ETAPA_LABEL.get(etapa, "Foco del método") if etapa else "Foco del método"
    etapa_prom = (agg.get("etapas_prom") or {}).get(etapa)
    checklist = agg.get("checklist") or []
    peor = checklist[0] if checklist else None

    partes = []
    if etapa and etapa_prom is not None:
        partes.append(
            f"Sobre {n} llamada(s) analizadas, la etapa más floja es "
            f"{ETAPA_LABEL.get(etapa, etapa).lower()} ({etapa_prom}/100)."
        )
    if peor:
        partes.append(f"La técnica menos aplicada: {peor['label'].lower()} (en el {peor['pct']}% de las llamadas).")
    partes.append("Enfoquen la semana ahí antes de sumar volumen.")

    return {
        "disponible": True,
        "titulo": titulo,
        "texto": " ".join(partes),
        "score": agg.get("score_prom"),
        "etapa_debil": etapa,
        "n": n,
    }


@router.get("/actividad")
def actividad(user: dict = Depends(get_current_user)) -> list[dict]:
    """Feed de actividad reciente del workspace: cierres, no-shows, transcripts, sets."""
    team = user.get("team_id")
    if not team:
        return []
    sb = get_supabase_admin()

    calls = (
        sb.table("calls").select("closer_id, lead_id, outcome, deal_value, created_at")
        .eq("team_id", team).order("created_at", desc=True).limit(15).execute().data or []
    )
    recs = (
        sb.table("call_recordings").select("closer_id, lead_id, title, ingested_at")
        .eq("team_id", team).order("ingested_at", desc=True).limit(10).execute().data or []
    )
    sums = (
        sb.table("setter_summaries").select("setter_id, lead_id, agendado, created_at")
        .eq("team_id", team).order("created_at", desc=True).limit(10).execute().data or []
    )

    # Resolver nombres de usuarios y leads en batch.
    uids = {r.get("closer_id") for r in calls} | {r.get("closer_id") for r in recs} | {s.get("setter_id") for s in sums}
    lids = {r.get("lead_id") for r in calls} | {r.get("lead_id") for r in recs} | {s.get("lead_id") for s in sums}
    uids.discard(None); lids.discard(None)
    users = (sb.table("users").select("id, nombre, email").in_("id", list(uids)).execute().data or []) if uids else []
    leads = (sb.table("leads").select("id, nombre").in_("id", list(lids)).execute().data or []) if lids else []
    unombre = {u["id"]: _corto(u.get("nombre"), u.get("email")) for u in users}
    lnombre = {l["id"]: (l.get("nombre") or "un lead") for l in leads}

    OUTCOME = {
        "cerro":       ("cerro",   lambda c, lead: f"cerró con {lead} — {_money(c.get('deal_value'))}"),
        "no_cerro":    ("neutral", lambda c, lead: f"no cerró con {lead}"),
        "seguimiento": ("neutral", lambda c, lead: f"dejó en seguimiento a {lead}"),
        "no_show":     ("neg",     lambda c, lead: f"— no show, {lead}"),
    }

    eventos = []
    for c in calls:
        tipo, fn = OUTCOME.get(c.get("outcome") or "", (None, None))
        if not tipo:
            continue
        dt = _parse_dt(c.get("created_at"))
        eventos.append({
            "tipo": tipo,
            "nombre": unombre.get(c.get("closer_id"), "Un closer"),
            "texto": fn(c, lnombre.get(c.get("lead_id"), "un lead")),
            "hace": _hace(dt), "_ts": dt,
        })
    for r in recs:
        dt = _parse_dt(r.get("ingested_at"))
        detalle = lnombre.get(r.get("lead_id")) or r.get("title") or "una call"
        eventos.append({
            "tipo": "info",
            "nombre": unombre.get(r.get("closer_id"), "Un closer"),
            "texto": f"cargó transcript de call — {detalle}",
            "hace": _hace(dt), "_ts": dt,
        })
    for s in sums:
        dt = _parse_dt(s.get("created_at"))
        lead = lnombre.get(s.get("lead_id"), "un lead")
        texto = f"agendó reunión con {lead}" if s.get("agendado") else f"cargó resumen de setting — {lead}"
        eventos.append({
            "tipo": "cyan" if s.get("agendado") else "info",
            "nombre": unombre.get(s.get("setter_id"), "Un setter"),
            "texto": texto,
            "hace": _hace(dt), "_ts": dt,
        })

    eventos.sort(key=lambda e: e["_ts"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    for e in eventos:
        e.pop("_ts", None)
    return eventos[:8]
