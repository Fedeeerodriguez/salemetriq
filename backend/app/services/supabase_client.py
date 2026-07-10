"""Cliente Supabase singleton (anon + service_role).

Si no hay SUPABASE_SERVICE_ROLE_KEY, cae a un fake EN MEMORIA (dev/testing local)
— ver services/fake_db.py. Así el flujo completo corre sin un proyecto real.
"""
import logging

from supabase import Client, create_client

from ..config import settings

logger = logging.getLogger(__name__)

# Modo dev: sin service_role key → base en memoria.
USE_FAKE = not settings.SUPABASE_SERVICE_ROLE_KEY

_client: Client | None = None
_admin_client = None


def get_supabase() -> Client:
    """Cliente anon — respeta RLS. Para operaciones en nombre del usuario."""
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _client


def get_supabase_admin() -> Client:
    """Cliente service_role — saltea RLS. Solo backend (ingesta + análisis IA).

    Si falta la service_role key cae a la anon, pero con RLS activo la anon está
    DENEGADA en todo → el backend leería vacío y los inserts fallarían. Por eso lo
    avisamos con un ERROR bien visible en vez de romper en silencio.
    """
    global _admin_client
    if _admin_client is None:
        if USE_FAKE:
            from .fake_db import FakeSupabase
            logger.warning(
                "DEV MODE: sin SUPABASE_SERVICE_ROLE_KEY → usando base EN MEMORIA "
                "(fake_db). Los datos NO se persisten. Solo para desarrollo/testing."
            )
            _admin_client = FakeSupabase()
            return _admin_client
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not key:
            logger.error(
                "SUPABASE_SERVICE_ROLE_KEY no está configurada — usando la anon key. "
                "Con RLS activo el backend NO podrá leer ni escribir. Configurá la "
                "service_role key en el entorno."
            )
            key = settings.SUPABASE_ANON_KEY
        _admin_client = create_client(settings.SUPABASE_URL, key)
    return _admin_client
