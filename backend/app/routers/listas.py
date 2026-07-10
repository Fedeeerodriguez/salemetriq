"""Router de listas — colecciones de perfiles para outreach manual + export CSV.

La app NO contacta: solo agrupa perfiles y deja gestionar el estado del follow-up
(nuevo/contactado/respondió/descartado) a mano, y exporta a CSV.
"""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.auth import get_current_user
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/listas", tags=["listas"])


class ListaIn(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str | None = None


class AgregarPerfiles(BaseModel):
    usernames: list[str]


class EstadoContacto(BaseModel):
    estado_contacto: str | None = None
    nota: str | None = None


ESTADOS = {"nuevo", "contactado", "respondio", "descartado"}


@router.get("")
def listar(user: dict = Depends(get_current_user)) -> list[dict]:
    sb = get_supabase_admin()
    res = sb.table("listas").select("*").order("created_at", desc=True).execute()
    listas = res.data or []
    # contar perfiles por lista
    for l in listas:
        c = sb.table("lista_perfiles").select("id", count="exact").eq("lista_id", l["id"]).execute()
        l["total"] = c.count or 0
    return listas


@router.post("", status_code=201)
def crear(body: ListaIn, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    res = sb.table("listas").insert({
        "nombre": body.nombre.strip(), "descripcion": body.descripcion, "owner": user["id"],
    }).execute()
    return res.data[0]


@router.delete("/{lista_id}", status_code=204)
def eliminar(lista_id: str, user: dict = Depends(get_current_user)) -> None:
    sb = get_supabase_admin()
    sb.table("listas").delete().eq("id", lista_id).execute()


@router.get("/{lista_id}")
def detalle(lista_id: str, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    lista = sb.table("listas").select("*").eq("id", lista_id).limit(1).execute().data
    if not lista:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    # join manual: lista_perfiles + ig_profiles
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


@router.post("/{lista_id}/perfiles")
def agregar(lista_id: str, body: AgregarPerfiles, user: dict = Depends(get_current_user)) -> dict:
    sb = get_supabase_admin()
    filas = [{"lista_id": lista_id, "username": u.lower(), "estado_contacto": "nuevo"} for u in body.usernames if u]
    if not filas:
        return {"agregados": 0}
    # upsert ignora los que ya estaban (unique lista_id+username)
    sb.table("lista_perfiles").upsert(filas, on_conflict="lista_id,username", ignore_duplicates=True).execute()
    return {"agregados": len(filas)}


@router.patch("/{lista_id}/perfiles/{username}")
def cambiar_estado(lista_id: str, username: str, body: EstadoContacto, user: dict = Depends(get_current_user)) -> dict:
    if body.estado_contacto and body.estado_contacto not in ESTADOS:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Opciones: {sorted(ESTADOS)}")
    sb = get_supabase_admin()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    sb.table("lista_perfiles").update(updates).eq("lista_id", lista_id).eq("username", username.lower()).execute()
    return {"ok": True}


@router.delete("/{lista_id}/perfiles/{username}", status_code=204)
def quitar(lista_id: str, username: str, user: dict = Depends(get_current_user)) -> None:
    sb = get_supabase_admin()
    sb.table("lista_perfiles").delete().eq("lista_id", lista_id).eq("username", username.lower()).execute()


@router.get("/{lista_id}/export")
def exportar_csv(lista_id: str, user: dict = Depends(get_current_user)) -> StreamingResponse:
    data = detalle(lista_id, user)
    perfiles = data["perfiles"]

    buff = io.StringIO()
    buff.write("﻿")  # BOM para que Excel abra UTF-8 bien
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
