"""Da transcripts variados a las grabaciones demo y las re-analiza con Claude real,
para que el drawer de Call Analysis muestre coaching completo (fortalezas, mejoras,
próxima acción). Solo toca grabaciones is_demo=true.

Uso (desde backend/):  .venv/Scripts/python scripts/enrich_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routers.grabaciones import _persistir_analisis
from app.services.supabase_client import get_supabase_admin

sb = get_supabase_admin()

TRANSCRIPTS = [
    # 1) Cierre fuerte
    "Closer: Antes de mostrarte nada, contame qué te trajo a esta llamada.\n"
    "Prospecto: Estamos facturando 40k/mes pero el equipo comercial improvisa y perdemos deals.\n"
    "Closer: ¿Cuántos deals se caen por mes y cuánto valdría recuperar la mitad?\n"
    "Prospecto: Unos 6, y cada uno ronda los 3k. Sería recuperar 9k mensuales.\n"
    "Closer: O sea 108k al año en la mesa. Si te muestro cómo trackear cada llamada para tapar esa fuga, "
    "¿tendría sentido arrancar este mes?\n"
    "Prospecto: Sí, me cierra.\n"
    "Closer: Perfecto. Te paso la propuesta hoy y coordinamos onboarding el jueves. ¿Quién más firma?\n"
    "Prospecto: Solo yo. Dale, jueves.",
    # 2) Se pierde en precio
    "Closer: Bueno, te muestro el producto directamente así vemos si te sirve.\n"
    "Prospecto: Ok… se ve bien. ¿Cuánto sale?\n"
    "Closer: 2.500 por mes.\n"
    "Prospecto: Uh, es caro para nosotros ahora.\n"
    "Closer: Es que tiene un montón de features.\n"
    "Prospecto: Sí pero no sé, lo tengo que pensar.\n"
    "Closer: Dale, cualquier cosa me escribís.",
    # 3) Rusheó el descubrimiento
    "Closer: Hola, mirá, básicamente nosotros hacemos telemetría de ventas. Te tiro el pitch.\n"
    "Prospecto: Ok.\n"
    "Closer: Trackeamos llamadas, damos score, todo automático. ¿Te sirve?\n"
    "Prospecto: Puede ser, pero no me preguntaste qué necesito.\n"
    "Closer: Cierto, ¿qué necesitás?\n"
    "Prospecto: Tengo que cortar, mandame info por mail.",
    # 4) Buen descubrimiento, cierre flojo
    "Closer: Contame cómo venís con el seguimiento de tus closers.\n"
    "Prospecto: Mal, no tengo visibilidad de qué pasa en las llamadas.\n"
    "Closer: ¿Y eso qué costo te genera hoy?\n"
    "Prospecto: No sé medirlo, esa es la parte fea. Siento que dejo plata en la mesa.\n"
    "Closer: Claro. ¿Cuántas llamadas hace el equipo por semana?\n"
    "Prospecto: Unas 50.\n"
    "Closer: Buenísimo, con eso ya tenés volumen para analizar patrones. Te muestro el dashboard.\n"
    "Prospecto: Me interesa. ¿Cómo sigo?\n"
    "Closer: Eh… te mando material y vemos.",
]

recs = (
    sb.table("call_recordings").select("id, title, transcript, is_demo")
    .eq("is_demo", True).order("recorded_at", desc=True).execute().data or []
)
print(f"Re-analizando {len(recs)} grabaciones demo…")
for i, r in enumerate(recs):
    t = TRANSCRIPTS[i % len(TRANSCRIPTS)]
    sb.table("call_recordings").update({"transcript": t}).eq("id", r["id"]).execute()
    r["transcript"] = t
    sb.table("analysis_runs").delete().eq("target_id", r["id"]).execute()  # limpia el análisis viejo
    try:
        run = _persistir_analisis(sb, r)
        print(f"  [OK] {r['title']} -> score {run.get('score')}")
    except Exception as e:
        print(f"  [FALLO] {r['title']}: {e}")

print("[OK] Grabaciones demo enriquecidas con coaching real.")
