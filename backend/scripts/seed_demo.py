"""Siembra datos demo en Supabase para ver la plataforma poblada.

Idempotente: limpia las tablas de datos (no los usuarios), reupserta el equipo
demo y vuelve a insertar leads, llamadas, resúmenes, grabaciones y análisis.

Uso (desde backend/):
    .venv/Scripts/python scripts/seed_demo.py
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

# Permitir `import app...` al correr como script (agrega backend/ al path).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth import hash_password
from app.services.supabase_client import get_supabase_admin

random.seed(42)
sb = get_supabase_admin()
now = datetime.now(timezone.utc)

ALL = "00000000-0000-0000-0000-000000000000"  # centinela para "borrar todo"


def iso(dt: datetime) -> str:
    return dt.isoformat()


def ago(days: float) -> datetime:
    return now - timedelta(days=days, hours=random.uniform(0, 12))


# ── 1. Limpieza SOLO de datos demo (nunca toca datos reales) ─────────────────
print("Limpiando datos demo previos…")
# transcript_chunks cae por cascada al borrar calls. Orden por FK.
for tabla in ["analysis_runs", "call_recordings", "calls",
              "setter_summaries", "metrics_daily", "leads"]:
    try:
        sb.table(tabla).delete().eq("is_demo", True).execute()
    except Exception as e:
        print(f"  (skip {tabla}: {e})")

# ── 2. Equipo demo (reutiliza si ya existe) ──────────────────────────────────
print("Equipo + usuarios demo…")
existing_team = sb.table("teams").select("id").eq("is_demo", True).limit(1).execute().data
if existing_team:
    team_id = existing_team[0]["id"]
else:
    team_id = sb.table("teams").insert(
        {"nombre": "Equipo Comercial (Demo)", "is_demo": True}
    ).execute().data[0]["id"]

PWD = hash_password("Demo1234!")


def demo_email(nombre):
    return nombre.lower().replace("á", "a").replace("é", "e").replace("í", "i") \
        .replace("ó", "o").replace("ú", "u").replace(" ", ".") + ".demo@salemetriq.com"


def user_row(nombre, rol):
    return {"team_id": team_id, "email": demo_email(nombre), "password_hash": PWD,
            "nombre": nombre, "rol": rol, "activo": True, "is_demo": True}


CLOSERS = ["Fede Rodríguez", "Nico Fernández", "Marina García", "Tomás López", "Paula Vega"]
SETTERS = ["Lucas Díaz", "Sofía Romero", "Martín Sosa", "Caro Ibáñez"]

rows = [user_row(n, "closer") for n in CLOSERS] + [user_row(n, "setter") for n in SETTERS]
# Usuario demo: el único que ve estos datos (rol admin, is_demo=true).
rows.append({"team_id": team_id, "email": "demo@salemetriq.com",
             "password_hash": hash_password("Demo2026!"),
             "nombre": "Usuario Demo", "rol": "admin", "activo": True, "is_demo": True})

users = sb.table("users").upsert(rows, on_conflict="email").execute().data
by_email = {u["email"]: u for u in users}
closers = [by_email[user_row(n, "closer")["email"]] for n in CLOSERS]
setters = [by_email[user_row(n, "setter")["email"]] for n in SETTERS]
closer_ids = [c["id"] for c in closers]
setter_ids = [s["id"] for s in setters]

# ── 3. Leads ─────────────────────────────────────────────────────────────────
print("Leads…")
PROSPECTOS = [
    "Agencia Norte", "Estudio Delta", "Marina Solís", "Lucas Ferrari", "Growth Media",
    "Paula Ventura", "Consultora Ápex", "Nacho Beltrán", "Vértice Digital", "Sabrina Ruiz",
    "Roca Consulting", "Damián Ortiz", "Costa Marketing", "Julieta Peralta", "Fábrica de Leads",
    "Bruno Cáceres",
]
ORIGENES = ["Instagram Ads", "Referido", "YouTube", "Webinar", "Cold Email", "Landing"]
ESTADOS = ["nuevo", "agendado", "en_proceso", "ganado", "perdido"]

lead_rows = []
for i, p in enumerate(PROSPECTOS):
    lead_rows.append({
        "team_id": team_id,
        "nombre": p,
        "contacto": p.lower().replace(" ", ".") + "@mail.com",
        "origen": random.choice(ORIGENES),
        "setter_id": random.choice(setter_ids),
        "closer_id": random.choice(closer_ids),
        "estado": random.choice(ESTADOS),
        "is_demo": True,
    })
leads = sb.table("leads").insert(lead_rows).execute().data

# ── 4. Calls (llamadas de closers) ───────────────────────────────────────────
print("Llamadas…")
OUTCOMES = ["cerro"] * 32 + ["no_cerro"] * 30 + ["seguimiento"] * 23 + ["no_show"] * 15
TRANSCRIPTS = [
    "Closer: Contame un poco cómo venís manejando la parte comercial hoy.\nProspecto: "
    "Y… tenemos leads pero nos cuesta cerrarlos. El equipo improvisa mucho.\nCloser: "
    "Claro, ahí es justo donde entramos nosotros. ¿Cuánto estás facturando por mes hoy?",
    "Closer: ¿Qué te frenó la última vez que evaluaste algo así?\nProspecto: "
    "El precio, sinceramente. Me pareció caro para el momento.\nCloser: "
    "Te entiendo. Pensemos en el costo de no resolverlo: ¿cuántas ventas se te escapan por mes?",
    "Closer: Perfecto, entonces coincidimos en el problema. Te muestro cómo lo resolvemos.\n"
    "Prospecto: Dale, pero necesito consultarlo con mi socio.\nCloser: "
    "Buenísimo. ¿Qué necesitaría ver tu socio para decir que sí?",
    "Closer: Si esto te ahorra 10 horas semanales, ¿tendría sentido arrancar este mes?\n"
    "Prospecto: Sí, me cierra. ¿Cómo seguimos?\nCloser: Te paso la propuesta y coordinamos el onboarding.",
]
call_rows = []
for _ in range(34):
    outcome = random.choice(OUTCOMES)
    cerro = outcome == "cerro"
    call_rows.append({
        "closer_id": random.choice(closer_ids),
        "lead_id": random.choice(leads)["id"],
        "fecha": iso(ago(random.uniform(0, 56))),
        "duracion_seg": random.randint(720, 3300),
        "outcome": outcome,
        "deal_value": round(random.uniform(1800, 6200), 2) if cerro else 0,
        "transcript": random.choice(TRANSCRIPTS),
        "is_demo": True,
    })
calls = sb.table("calls").insert(call_rows).execute().data

# ── 5. Análisis IA de algunas llamadas ───────────────────────────────────────
print("Análisis de llamadas…")
SENTIMENTS = ["positivo", "neutral", "negativo"]
OBJECIONES = [
    [{"tipo": "precio", "momento": "min 22", "resuelta": False}],
    [{"tipo": "tiempo", "momento": "min 14", "resuelta": True}],
    [{"tipo": "autoridad", "momento": "min 18", "resuelta": False},
     {"tipo": "precio", "momento": "min 26", "resuelta": True}],
    [],
]
RESUMENES = [
    "Buena apertura y descubrimiento. Se pierde en el cierre: no pide la venta con claridad.",
    "Manejo sólido de objeción de precio anclando en costo de oportunidad. Cierre limpio.",
    "Descubrimiento flojo, saltó al pitch demasiado rápido. La objeción quedó sin resolver.",
    "Rapport excelente. Faltó crear urgencia antes de proponer próximos pasos.",
]
analysis_rows = []
for c in random.sample(calls, 14):
    dims = {k: random.randint(45, 95) for k in ["apertura", "descubrimiento", "pitch", "objeciones", "cierre"]}
    analysis_rows.append({
        "target_tipo": "call",
        "target_id": c["id"],
        "modelo": "claude-sonnet-5",
        "score": round(sum(dims.values()) / len(dims), 1),
        "sentiment": random.choice(SENTIMENTS),
        "objeciones": random.choice(OBJECIONES),
        "tags": list(dims.keys()),
        "resumen": random.choice(RESUMENES),
        "raw": {"dimensiones": dims},
        "is_demo": True,
    })

# ── 6. Resúmenes de setters ──────────────────────────────────────────────────
print("Resúmenes de setters…")
CALIF = ["Alto interés", "Interés medio", "Bajo interés", "Muy calificado", "A nutrir"]
TEXTOS = [
    "Prospecto dueño de agencia, factura ~8k/mes. Dolor claro con cierres. Agendado para el jueves.",
    "Le interesa pero está frío, pidió material antes de reunión. Nurturing.",
    "Muy caliente, ya probó competencia y no le funcionó. Alta intención de compra.",
    "Presupuesto ajustado este mes, reagendar para el mes que viene.",
]
summ_rows = []
for _ in range(18):
    tipo = random.choice(["texto", "audio"])
    agendado = random.random() < 0.62
    summ_rows.append({
        "setter_id": random.choice(setter_ids),
        "lead_id": random.choice(leads)["id"],
        "fecha": iso(ago(random.uniform(0, 40))),
        "tipo": tipo,
        "texto": random.choice(TEXTOS),
        "audio_url": "https://demo.salemetriq.com/audio/setting-demo.ogg" if tipo == "audio" else None,
        "lead_qualification": random.choice(CALIF),
        "agendado": agendado,
        "is_demo": True,
    })
sb.table("setter_summaries").insert(summ_rows).execute()

# ── 7. Grabaciones (Fathom) + su análisis ────────────────────────────────────
print("Grabaciones + análisis…")
REC_TRANSCRIPT = (
    "Closer: Gracias por el tiempo. Antes de mostrarte nada, contame qué te trajo a esta llamada.\n"
    "Prospecto: Estoy escalando el equipo comercial y siento que perdemos plata en el proceso de venta.\n"
    "Closer: ¿Cómo medís hoy esa pérdida?\nProspecto: No la mido, esa es la parte fea.\n"
    "Closer: Entonces primero necesitás visibilidad. Te muestro cómo trackeamos cada llamada…\n"
    "Prospecto: Eso es exactamente lo que me falta. ¿Cuánto sale?\n"
    "Closer: Depende del volumen, pero pensemos primero en el retorno. Si recuperás una venta por semana…"
)
rec_rows = []
for i in range(8):
    closer = random.choice(closers)
    lead = random.choice(leads)
    analizado = i < 5
    rec_rows.append({
        "provider": "fathom",
        "external_id": f"fathom_demo_{1000 + i}",
        "title": f"Discovery — {lead['nombre']} × {closer['nombre'].split()[0]}",
        "recording_url": f"https://fathom.video/calls/demo{i}",
        "transcript": REC_TRANSCRIPT,
        "language": "es",
        "duration_seg": random.randint(1500, 3200),
        "recorded_at": iso(ago(random.uniform(0, 30))),
        "participants": [
            {"nombre": closer["nombre"], "rol": "closer"},
            {"nombre": lead["nombre"], "rol": "prospecto"},
        ],
        "closer_id": closer["id"],
        "status": "analizado" if analizado else "nuevo",
        "is_demo": True,
    })
recs = sb.table("call_recordings").insert(rec_rows).execute().data

for i, r in enumerate(recs):
    if r["status"] != "analizado":
        continue
    dims = {k: random.randint(50, 93) for k in ["apertura", "descubrimiento", "pitch", "objeciones", "cierre"]}
    analysis_rows.append({
        "target_tipo": "call_recording",
        "target_id": r["id"],
        "modelo": "claude-sonnet-5",
        "score": round(sum(dims.values()) / len(dims), 1),
        "sentiment": random.choice(SENTIMENTS),
        "objeciones": random.choice(OBJECIONES),
        "tags": list(dims.keys()),
        "resumen": random.choice(RESUMENES),
        "raw": {"dimensiones": dims, "recomendaciones": [
            "Pedir la venta de forma explícita antes de cerrar la llamada.",
            "Anclar el precio en el costo de oportunidad, no en el ticket.",
        ]},
        "is_demo": True,
    })

sb.table("analysis_runs").insert(analysis_rows).execute()

# ── Resumen ──────────────────────────────────────────────────────────────────
print("\n[OK] Datos demo cargados:")
print(f"   {len(closers)} closers · {len(setters)} setters")
print(f"   {len(leads)} leads · {len(calls)} llamadas · {len(summ_rows)} resúmenes")
print(f"   {len(recs)} grabaciones · {len(analysis_rows)} análisis")
