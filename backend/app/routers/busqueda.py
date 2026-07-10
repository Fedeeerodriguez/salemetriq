"""Router de búsqueda — encola un scrape_job y lo corre en background.

Flujo: POST /api/busqueda crea el job (estado 'pendiente') y dispara el runner en
background; el frontend consulta GET /api/busqueda/{id} para ver el progreso.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ..services.auth import get_current_user
from ..services.ig_jobs import run_job
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/busqueda", tags=["busqueda"])

ANGULOS = {"hashtag", "keyword", "followers", "ubicacion"}


class Filtros(BaseModel):
    limite: int | None = None
    min_followers: int | None = None
    max_followers: int | None = None
    solo_business: bool | None = None
    con_contacto: bool | None = None
    min_score: int | None = None


class BusquedaIn(BaseModel):
    angulo: str
    query: str = Field(min_length=1)
    nicho_id: str | None = None
    filtros: Filtros = Filtros()


@router.post("", status_code=202)
def crear_busqueda(
    body: BusquedaIn,
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict:
    if body.angulo not in ANGULOS:
        raise HTTPException(status_code=400, detail=f"Ángulo inválido. Opciones: {sorted(ANGULOS)}")

    sb = get_supabase_admin()
    payload = {
        "angulo": body.angulo,
        "query": body.query.strip(),
        "nicho_id": body.nicho_id,
        "filtros": body.filtros.model_dump(exclude_none=True),
        "estado": "pendiente",
        "created_by": user["id"],
    }
    res = sb.table("scrape_jobs").insert(payload).execute()
    job = res.data[0]

    background.add_task(run_job, job["id"])
    return job


@router.get("/{job_id}")
def estado(job_id: str, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    res = sb.table("scrape_jobs").select("*").eq("id", job_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return res.data[0]


@router.get("")
def historial(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = sb.table("scrape_jobs").select("*").order("created_at", desc=True).limit(50).execute()
    return res.data or []
