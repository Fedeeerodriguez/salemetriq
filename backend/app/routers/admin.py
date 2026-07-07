"""Router de plataforma (superadmin) — alta y listado de clientes (workspaces).

Solo accesible por usuarios is_superadmin (nosotros). Crear un cliente = crear un
workspace (team) + su usuario admin dueño. El resto de los usuarios internos los
crea después ese admin desde su propio workspace.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..services.auth import hash_password, require_superadmin
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class WorkspaceCreate(BaseModel):
    nombre: str                 # nombre del cliente/workspace
    plan: str = "standard"
    admin_email: EmailStr       # dueño del workspace
    admin_nombre: str
    admin_password: str


# ── Listar workspaces (clientes) ─────────────────────────────────────────────
@router.get("/workspaces")
def listar_workspaces(user: dict = Depends(require_superadmin)) -> list[dict]:
    sb = get_supabase_admin()
    teams = sb.table("teams").select("id, nombre, plan, owner_id, is_demo, created_at").order("created_at").execute().data or []
    if not teams:
        return []

    users = sb.table("users").select("id, email, nombre, rol, team_id, activo").execute().data or []
    by_team: dict[str, list] = {}
    owners: dict[str, dict] = {}
    for u in users:
        by_team.setdefault(u.get("team_id"), []).append(u)
        owners[u["id"]] = u

    out = []
    for t in teams:
        miembros = [m for m in by_team.get(t["id"], []) if m.get("activo", True)]
        counts = {"admin": 0, "closer": 0, "setter": 0}
        for m in miembros:
            if m["rol"] in counts:
                counts[m["rol"]] += 1
        owner = owners.get(t.get("owner_id"))
        out.append({
            "id": t["id"],
            "nombre": t["nombre"],
            "plan": t.get("plan"),
            "is_demo": t.get("is_demo"),
            "owner_email": owner["email"] if owner else None,
            "owner_nombre": owner["nombre"] if owner else None,
            "counts": counts,
            "total_miembros": len(miembros),
        })
    return out


# ── Crear cliente (workspace + admin dueño) ──────────────────────────────────
@router.post("/workspaces")
def crear_workspace(body: WorkspaceCreate, user: dict = Depends(require_superadmin)) -> dict:
    if len(body.admin_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña del admin debe tener al menos 6 caracteres")

    sb = get_supabase_admin()
    email = body.admin_email.lower()
    if sb.table("users").select("id").eq("email", email).limit(1).execute().data:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    # 1) workspace
    team = sb.table("teams").insert({"nombre": body.nombre, "plan": body.plan, "is_demo": False}).execute().data[0]

    # 2) admin dueño
    admin = sb.table("users").insert({
        "team_id": team["id"],
        "email": email,
        "password_hash": hash_password(body.admin_password),
        "nombre": body.admin_nombre,
        "rol": "admin",
        "activo": True,
        "is_demo": False,
        "is_superadmin": False,
    }).execute().data[0]

    # 3) marcar dueño en el workspace
    sb.table("teams").update({"owner_id": admin["id"]}).eq("id", team["id"]).execute()

    return {
        "workspace": {"id": team["id"], "nombre": team["nombre"], "plan": team["plan"]},
        "admin": {"id": admin["id"], "email": admin["email"], "nombre": admin["nombre"]},
    }
