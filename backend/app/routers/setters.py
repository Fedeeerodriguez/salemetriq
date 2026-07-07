"""Router de setters — listado y resúmenes (audio/texto) por setter."""
from fastapi import APIRouter, Depends

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/setters", tags=["setters"])


@router.get("")
def listar_setters(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = (
        sb.table("users").select("id, nombre, email, rol")
        .eq("rol", "setter").eq("is_demo", bool(user.get("is_demo"))).execute()
    )
    return res.data or []


@router.get("/{setter_id}/resumenes")
def resumenes_de_setter(setter_id: str, user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = (
        sb.table("setter_summaries")
        .select("id, fecha, tipo, texto, audio_url, lead_qualification, agendado")
        .eq("setter_id", setter_id)
        .eq("is_demo", bool(user.get("is_demo")))
        .order("fecha", desc=True)
        .execute()
    )
    return res.data or []
