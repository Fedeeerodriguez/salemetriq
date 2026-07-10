"""Router de perfiles — listado con filtros para la tabla de resultados."""
from fastapi import APIRouter, Depends, Query

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/perfiles", tags=["perfiles"])


@router.get("")
def listar(
    user: dict = Depends(get_current_user),
    nicho_id: str | None = None,
    min_followers: int | None = None,
    max_followers: int | None = None,
    solo_business: bool | None = None,
    con_contacto: bool | None = None,
    min_score: int | None = None,
    buscar: str | None = None,
    orden: str = Query("score", pattern="^(score|followers|recientes)$"),
    limit: int = Query(100, le=500),
    offset: int = 0,
) -> dict:
    sb = get_supabase_admin()
    q = sb.table("ig_profiles").select("*", count="exact")

    if nicho_id:
        q = q.eq("nicho_id", nicho_id)
    if min_followers is not None:
        q = q.gte("followers", min_followers)
    if max_followers is not None:
        q = q.lte("followers", max_followers)
    if solo_business:
        q = q.eq("is_business", True)
    if min_score is not None:
        q = q.gte("score_nicho", min_score)
    if buscar:
        term = f"%{buscar.strip()}%"
        q = q.or_(f"username.ilike.{term},full_name.ilike.{term},bio.ilike.{term}")
    if con_contacto:
        # tiene email O web público
        q = q.or_("email_publico.not.is.null,external_url.not.is.null")

    if orden == "followers":
        q = q.order("followers", desc=True)
    elif orden == "recientes":
        q = q.order("scraped_at", desc=True)
    else:
        q = q.order("score_nicho", desc=True)

    res = q.range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "total": res.count or 0}


@router.get("/{username}")
def detalle(username: str, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    res = sb.table("ig_profiles").select("*").eq("username", username.lower()).limit(1).execute()
    return res.data[0] if res.data else {}
