"""Re-etiqueta la data existente (del primer seed) como demo — NO destructivo.

- Marca is_demo=true en todas las filas de datos y en los usuarios closer/setter.
- Crea/asegura el usuario demo (único que ve la data demo).
- Asegura que el admin real quede como NO demo (ve solo datos reales).

Uso (desde backend/):
    .venv/Scripts/python scripts/tag_demo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auth import hash_password
from app.services.supabase_client import get_supabase_admin

sb = get_supabase_admin()
ALL = "00000000-0000-0000-0000-000000000000"

print("Re-etiquetando data existente como demo…")
for t in ["leads", "calls", "setter_summaries", "call_recordings", "analysis_runs", "metrics_daily"]:
    try:
        r = sb.table(t).update({"is_demo": True}).neq("id", ALL).execute()
        print(f"  {t}: {len(r.data or [])} filas")
    except Exception as e:
        print(f"  (skip {t}: {e})")

print("Marcando closers/setters como demo…")
sb.table("users").update({"is_demo": True}).in_("rol", ["closer", "setter"]).execute()

print("Asegurando usuario demo…")
existing = sb.table("users").select("id").eq("email", "demo@salemetriq.com").execute().data
if existing:
    sb.table("users").update({"is_demo": True}).eq("email", "demo@salemetriq.com").execute()
else:
    sb.table("users").insert({
        "email": "demo@salemetriq.com",
        "password_hash": hash_password("Demo2026!"),
        "nombre": "Usuario Demo",
        "rol": "admin",
        "activo": True,
        "is_demo": True,
    }).execute()

print("Asegurando que el admin real NO sea demo…")
sb.table("users").update({"is_demo": False}).eq("email", "admin@salemetriq.com").execute()

print("[OK] Data demo aislada. Solo demo@salemetriq.com la ve.")
