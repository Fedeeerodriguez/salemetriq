"""Router de nichos — CRUD de la definición reutilizable de un nicho.

Un nicho = nombre + keywords (esperadas en la bio) + hashtags + cuentas semilla.
Se usa para orientar la búsqueda y para el scoring de afinidad.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/nichos", tags=["nichos"])


class NichoIn(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str | None = None
    keywords: list[str] = []
    hashtags: list[str] = []
    cuentas_semilla: list[str] = []
    usa_ia: bool = False


class NichoOut(NichoIn):
    id: str


def _limpiar_lista(xs: list[str]) -> list[str]:
    return [x.strip().lstrip("@#").lower() for x in xs if x and x.strip()]


@router.get("", response_model=list[NichoOut])
def listar(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = sb.table("nichos").select("*").order("created_at", desc=True).execute()
    return res.data or []


@router.post("", response_model=NichoOut, status_code=201)
def crear(body: NichoIn, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    payload = {
        "nombre": body.nombre.strip(),
        "descripcion": body.descripcion,
        "keywords": _limpiar_lista(body.keywords),
        "hashtags": _limpiar_lista(body.hashtags),
        "cuentas_semilla": _limpiar_lista(body.cuentas_semilla),
        "usa_ia": body.usa_ia,
        "created_by": user["id"],
    }
    res = sb.table("nichos").insert(payload).execute()
    return res.data[0]


@router.put("/{nicho_id}", response_model=NichoOut)
def actualizar(nicho_id: str, body: NichoIn, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    payload = {
        "nombre": body.nombre.strip(),
        "descripcion": body.descripcion,
        "keywords": _limpiar_lista(body.keywords),
        "hashtags": _limpiar_lista(body.hashtags),
        "cuentas_semilla": _limpiar_lista(body.cuentas_semilla),
        "usa_ia": body.usa_ia,
    }
    res = sb.table("nichos").update(payload).eq("id", nicho_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Nicho no encontrado")
    return res.data[0]


@router.delete("/{nicho_id}", status_code=204)
def eliminar(nicho_id: str, user: dict = Depends(get_current_user)) -> None:
    sb = get_supabase_admin()
    sb.table("nichos").delete().eq("id", nicho_id).execute()
