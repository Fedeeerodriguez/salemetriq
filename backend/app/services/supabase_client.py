"""Cliente Supabase singleton (anon + service_role)."""
from supabase import Client, create_client

from ..config import settings

_client: Client | None = None
_admin_client: Client | None = None


def get_supabase() -> Client:
    """Cliente anon — respeta RLS. Para operaciones en nombre del usuario."""
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _client


def get_supabase_admin() -> Client:
    """Cliente service_role — saltea RLS. Solo backend (ingesta + análisis IA).

    Cae a la anon key si no hay service_role configurada, para no romper el arranque.
    """
    global _admin_client
    if _admin_client is None:
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        _admin_client = create_client(settings.SUPABASE_URL, key)
    return _admin_client
