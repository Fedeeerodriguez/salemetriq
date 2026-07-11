"""Routers del IG Prospector — todos bajo /api/igp/* y SOLO superadmin.

Reusan la auth de la plataforma (require_superadmin) y la data del schema `igp`.
`created_by` / `owner` guardan el id del usuario de la plataforma.
"""
import csv
import io

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.auth import require_superadmin
from ..services.supabase_client import get_supabase_igp
from .ig_jobs import run_job

# ── Nichos ───────────────────────────────────────────────────────────────────
nichos_router = APIRouter(prefix="/api/igp/nichos", tags=["igp-nichos"])


class NichoIn(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str | None = None
    keywords: list[str] = []
    hashtags: list[str] = []
    cuentas_semilla: list[str] = []
    usa_ia: bool = False


def _limpiar_lista(xs: list[str]) -> list[str]:
    return [x.strip().lstrip("@#").lower() for x in xs if x and x.strip()]


@nichos_router.get("")
def nichos_listar(user: dict = Depends(require_superadmin)) -> list[dict]:
    sb = get_supabase_igp()
    return sb.table("nichos").select("*").order("created_at", desc=True).execute().data or []


@nichos_router.post("", status_code=201)
def nichos_crear(body: NichoIn, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    payload = {
        "nombre": body.nombre.strip(), "descripcion": body.descripcion,
        "keywords": _limpiar_lista(body.keywords), "hashtags": _limpiar_lista(body.hashtags),
        "cuentas_semilla": _limpiar_lista(body.cuentas_semilla), "usa_ia": body.usa_ia,
        "created_by": user["id"],
    }
    return sb.table("nichos").insert(payload).execute().data[0]


@nichos_router.put("/{nicho_id}")
def nichos_actualizar(nicho_id: str, body: NichoIn, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    payload = {
        "nombre": body.nombre.strip(), "descripcion": body.descripcion,
        "keywords": _limpiar_lista(body.keywords), "hashtags": _limpiar_lista(body.hashtags),
        "cuentas_semilla": _limpiar_lista(body.cuentas_semilla), "usa_ia": body.usa_ia,
    }
    res = sb.table("nichos").update(payload).eq("id", nicho_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Nicho no encontrado")
    return res.data[0]


@nichos_router.delete("/{nicho_id}", status_code=204)
def nichos_eliminar(nicho_id: str, user: dict = Depends(require_superadmin)) -> None:
    get_supabase_igp().table("nichos").delete().eq("id", nicho_id).execute()


# ── Búsqueda ─────────────────────────────────────────────────────────────────
busqueda_router = APIRouter(prefix="/api/igp/busqueda", tags=["igp-busqueda"])

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


@busqueda_router.post("", status_code=202)
def busqueda_crear(body: BusquedaIn, background: BackgroundTasks, user: dict = Depends(require_superadmin)) -> dict:
    if body.angulo not in ANGULOS:
        raise HTTPException(status_code=400, detail=f"Ángulo inválido. Opciones: {sorted(ANGULOS)}")
    sb = get_supabase_igp()
    payload = {
        "angulo": body.angulo, "query": body.query.strip(), "nicho_id": body.nicho_id,
        "filtros": body.filtros.model_dump(exclude_none=True), "estado": "pendiente",
        "total_encontrados": 0, "total_nuevos": 0, "error_msg": None, "created_by": user["id"],
    }
    job = sb.table("scrape_jobs").insert(payload).execute().data[0]
    background.add_task(run_job, job["id"])
    return job


@busqueda_router.get("/{job_id}")
def busqueda_estado(job_id: str, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    res = sb.table("scrape_jobs").select("*").eq("id", job_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return res.data[0]


@busqueda_router.get("")
def busqueda_historial(user: dict = Depends(require_superadmin)) -> list[dict]:
    sb = get_supabase_igp()
    return sb.table("scrape_jobs").select("*").order("created_at", desc=True).limit(50).execute().data or []


# ── Perfiles ─────────────────────────────────────────────────────────────────
perfiles_router = APIRouter(prefix="/api/igp/perfiles", tags=["igp-perfiles"])


@perfiles_router.get("")
def perfiles_listar(
    user: dict = Depends(require_superadmin),
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
    sb = get_supabase_igp()
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
        q = q.or_("email_publico.not.is.null,external_url.not.is.null")

    if orden == "followers":
        q = q.order("followers", desc=True)
    elif orden == "recientes":
        q = q.order("scraped_at", desc=True)
    else:
        q = q.order("score_nicho", desc=True)

    res = q.range(offset, offset + limit - 1).execute()
    return {"items": res.data or [], "total": res.count or 0}


@perfiles_router.get("/{username}")
def perfiles_detalle(username: str, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    res = sb.table("ig_profiles").select("*").eq("username", username.lower()).limit(1).execute()
    return res.data[0] if res.data else {}


# ── Listas ───────────────────────────────────────────────────────────────────
listas_router = APIRouter(prefix="/api/igp/listas", tags=["igp-listas"])


class ListaIn(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str | None = None


class AgregarPerfiles(BaseModel):
    usernames: list[str]


class EstadoContacto(BaseModel):
    estado_contacto: str | None = None
    nota: str | None = None


ESTADOS = {"nuevo", "contactado", "respondio", "descartado"}


@listas_router.get("")
def listas_listar(user: dict = Depends(require_superadmin)) -> list[dict]:
    sb = get_supabase_igp()
    listas = sb.table("listas").select("*").order("created_at", desc=True).execute().data or []
    for l in listas:
        c = sb.table("lista_perfiles").select("id", count="exact").eq("lista_id", l["id"]).execute()
        l["total"] = c.count or 0
    return listas


@listas_router.post("", status_code=201)
def listas_crear(body: ListaIn, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    return sb.table("listas").insert({
        "nombre": body.nombre.strip(), "descripcion": body.descripcion, "owner": user["id"],
    }).execute().data[0]


@listas_router.delete("/{lista_id}", status_code=204)
def listas_eliminar(lista_id: str, user: dict = Depends(require_superadmin)) -> None:
    get_supabase_igp().table("listas").delete().eq("id", lista_id).execute()


@listas_router.get("/{lista_id}")
def listas_detalle(lista_id: str, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    lista = sb.table("listas").select("*").eq("id", lista_id).limit(1).execute().data
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    lp = sb.table("lista_perfiles").select("*").eq("lista_id", lista_id).execute().data or []
    usernames = [x["username"] for x in lp]
    perfiles_map: dict[str, dict] = {}
    for i in range(0, len(usernames), 200):
        lote = usernames[i:i + 200]
        pr = sb.table("ig_profiles").select("*").in_("username", lote).execute().data or []
        perfiles_map.update({p["username"]: p for p in pr})
    items = []
    for x in lp:
        items.append({**perfiles_map.get(x["username"], {"username": x["username"]}),
                      "estado_contacto": x.get("estado_contacto", "nuevo"), "nota": x.get("nota"),
                      "lp_id": x["id"]})
    return {"lista": lista[0], "perfiles": items}


@listas_router.post("/{lista_id}/perfiles")
def listas_agregar(lista_id: str, body: AgregarPerfiles, user: dict = Depends(require_superadmin)) -> dict:
    sb = get_supabase_igp()
    filas = [{"lista_id": lista_id, "username": u.lower(), "estado_contacto": "nuevo"} for u in body.usernames if u]
    if not filas:
        return {"agregados": 0}
    sb.table("lista_perfiles").upsert(filas, on_conflict="lista_id,username", ignore_duplicates=True).execute()
    return {"agregados": len(filas)}


@listas_router.patch("/{lista_id}/perfiles/{username}")
def listas_cambiar_estado(lista_id: str, username: str, body: EstadoContacto, user: dict = Depends(require_superadmin)) -> dict:
    if body.estado_contacto and body.estado_contacto not in ESTADOS:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {sorted(ESTADOS)}")
    sb = get_supabase_igp()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    sb.table("lista_perfiles").update(updates).eq("lista_id", lista_id).eq("username", username.lower()).execute()
    return {"ok": True}


@listas_router.delete("/{lista_id}/perfiles/{username}", status_code=204)
def listas_quitar(lista_id: str, username: str, user: dict = Depends(require_superadmin)) -> None:
    get_supabase_igp().table("lista_perfiles").delete().eq("lista_id", lista_id).eq("username", username.lower()).execute()


@listas_router.get("/{lista_id}/export")
def listas_exportar_csv(lista_id: str, user: dict = Depends(require_superadmin)) -> StreamingResponse:
    data = listas_detalle(lista_id, user)
    perfiles = data["perfiles"]
    buff = io.StringIO()
    buff.write("﻿")  # BOM para Excel
    w = csv.writer(buff)
    w.writerow(["username", "nombre", "seguidores", "email", "web", "categoria",
                "score", "estado_contacto", "ig_url"])
    for p in perfiles:
        w.writerow([
            p.get("username", ""), p.get("full_name", ""), p.get("followers", ""),
            p.get("email_publico", ""), p.get("external_url", ""), p.get("category", ""),
            p.get("score_nicho", ""), p.get("estado_contacto", ""),
            p.get("ig_url", f"https://www.instagram.com/{p.get('username','')}/"),
        ])
    buff.seek(0)
    nombre = data["lista"]["nombre"].replace(" ", "_")
    return StreamingResponse(
        iter([buff.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="lista_{nombre}.csv"'},
    )


ROUTERS = [nichos_router, busqueda_router, perfiles_router, listas_router]
