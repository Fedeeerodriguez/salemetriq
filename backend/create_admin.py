"""Crea (o actualiza) el primer usuario admin en Supabase.

Uso (desde backend/, con el .env configurado):
    python create_admin.py admin@salemetriq.com  MiPassword123  "Nombre Apellido"
"""
import sys

from app.services.auth import hash_password
from app.services.supabase_client import get_supabase_admin


def main() -> None:
    if len(sys.argv) < 3:
        print("Uso: python create_admin.py <email> <password> [nombre]")
        raise SystemExit(1)

    email = sys.argv[1].lower()
    password = sys.argv[2]
    nombre = sys.argv[3] if len(sys.argv) > 3 else "Admin"

    sb = get_supabase_admin()
    payload = {
        "email": email,
        "password_hash": hash_password(password),
        "nombre": nombre,
        "rol": "admin",
        "activo": True,
    }
    # upsert por email
    res = sb.table("users").upsert(payload, on_conflict="email").execute()
    print("OK — usuario admin creado/actualizado:", email)
    print(res.data)


if __name__ == "__main__":
    main()
