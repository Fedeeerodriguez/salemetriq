"""Router de closers — listado y detalle con métricas de llamadas.

En Fase 0 devuelve lo que haya en Supabase. La lógica de scoring IA sobre los
transcripts se agrega en la Fase 3.
"""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/closers", tags=["closers"])


@router.get("")
def listar_closers(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = sb.table("users").select("id, nombre, email, rol").eq("rol", "closer").execute()
    return res.data or []


@router.get("/{closer_id}/llamadas")
def llamadas_de_closer(closer_id: str, user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = (
        sb.table("calls")
        .select("id, fecha, duracion_seg, outcome, deal_value, transcript")
        .eq("closer_id", closer_id)
        .order("fecha", desc=True)
        .execute()
    )
    return res.data or []
