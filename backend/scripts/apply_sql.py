"""Aplica un archivo .sql a Supabase (Postgres) vía el session pooler.

Uso (desde backend/):
    SMQ_DB_PASS='...' .venv/Scripts/python scripts/apply_sql.py ../db/igp_schema.sql

La password se pasa por env (tiene caracteres especiales) para no romper la
connection string.
"""
import os
import sys

import psycopg2

HOST = "aws-0-us-east-1.pooler.supabase.com"
PORT = 5432
DBNAME = "postgres"
USER = "postgres.ftyapmfywdruivtvdoio"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Uso: apply_sql.py <archivo.sql>")
    path = sys.argv[1]
    password = os.environ.get("SMQ_DB_PASS")
    if not password:
        sys.exit("Falta la env SMQ_DB_PASS con la password de la DB.")

    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = psycopg2.connect(
        host=HOST, port=PORT, dbname=DBNAME, user=USER, password=password, sslmode="require"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"[OK] Aplicado: {path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
