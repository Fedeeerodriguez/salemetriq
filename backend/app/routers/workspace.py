"""Router de workspace — gestión de usuarios internos por el admin del cliente.

Cada admin gestiona SOLO los usuarios de su propio workspace (team_id). Puede
crear/editar/desactivar admins, closers y setters. No puede crear superadmins ni
tocar otros workspaces.
"""
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..services.auth import get_current_user, hash_password, require_admin
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

ROLES_INTERNOS = {"admin", "closer", "setter"}


class MemberCreate(BaseModel):
    email: EmailStr
    nombre: str
    rol: str
    password: str


class MemberUpdate(BaseModel):
    nombre: str | None = None
    rol: str | None = None
    activo: bool | None = None
    password: str | None = None


class FathomEmail(BaseModel):
    fathom_email: str | None = None  # None/"" limpia el override


# ── Organigrama del workspace (personas + agentes IA) ────────────────────────
GRUPOS = [
    ("admin", "Administración"),
    ("closer", "Cierre"),
    ("setter", "Setting"),
]


@router.get("/equipo")
def equipo(user: dict = Depends(get_current_user)) -> dict:
    """Organigrama del workspace: miembros por rol con métricas rápidas + agentes IA."""
    team = user.get("team_id")
    if not team:
        raise HTTPException(status_code=404, detail="Sin workspace")
    sb = get_supabase_admin()

    t = sb.table("teams").select("nombre, owner_id").eq("id", team).limit(1).execute().data
    t = t[0] if t else {"nombre": None, "owner_id": None}

    users = (
        sb.table("users").select("id, nombre, email, rol, activo")
        .eq("team_id", team).eq("activo", True).execute().data or []
    )
    calls = sb.table("calls").select("closer_id, outcome, deal_value").eq("team_id", team).execute().data or []
    summ = sb.table("setter_summaries").select("setter_id, agendado").eq("team_id", team).execute().data or []

    # Agregados por persona
    ca: dict[str, dict] = {}
    for c in calls:
        a = ca.setdefault(c["closer_id"], {"n": 0, "cerr": 0})
        a["n"] += 1
        if c.get("outcome") == "cerro":
            a["cerr"] += 1
    sa: dict[str, dict] = {}
    for s in summ:
        a = sa.setdefault(s["setter_id"], {"n": 0, "ag": 0})
        a["n"] += 1
        if s.get("agendado"):
            a["ag"] += 1

    def kpis_de(u: dict) -> list[dict]:
        if u["rol"] == "closer":
            a = ca.get(u["id"], {"n": 0, "cerr": 0})
            rate = round(a["cerr"] / a["n"] * 100) if a["n"] else 0
            return [{"label": "Close rate", "value": f"{rate}%"}, {"label": "Llamadas", "value": a["n"]}]
        if u["rol"] == "setter":
            a = sa.get(u["id"], {"n": 0, "ag": 0})
            rate = round(a["ag"] / a["n"] * 100) if a["n"] else 0
            return [{"label": "Set rate", "value": f"{rate}%"}, {"label": "Resúmenes", "value": a["n"]}]
        return [{"label": "Rol", "value": "Admin"}]

    grupos = []
    for rol, label in GRUPOS:
        miembros = [
            {
                "id": u["id"], "nombre": u["nombre"], "email": u["email"], "rol": u["rol"],
                "es_owner": u["id"] == t.get("owner_id"),
                "kpis": kpis_de(u),
            }
            for u in users if u["rol"] == rol
        ]
        if miembros:
            grupos.append({"rol": rol, "label": label, "miembros": miembros})

    # ── Agentes IA (features de la plataforma, con uso real del workspace) ────
    runs = sb.table("analysis_runs").select("score, target_tipo").eq("team_id", team).execute().data or []
    rec_runs = [r for r in runs if r.get("target_tipo") == "call_recording"]
    scores = [r["score"] for r in rec_runs if r.get("score") is not None]
    score_prom = round(sum(scores) / len(scores)) if scores else None

    agentes = [
        {
            "nombre": "Analista IA",
            "tipo": "agente",
            "descripcion": "Analiza cada llamada y arma el coaching del closer.",
            "kpis": [
                {"label": "Analizadas", "value": len(rec_runs)},
                {"label": "Score prom", "value": f"{score_prom}" if score_prom is not None else "—"},
            ],
        },
    ]

    return {"workspace": t.get("nombre"), "grupos": grupos, "agentes": agentes}


# ── Info del workspace (para cualquier usuario del team) ─────────────────────
@router.get("")
def info(user: dict = Depends(get_current_user)) -> dict:
    team = user.get("team_id")
    if not team:
        raise HTTPException(status_code=404, detail="Sin workspace")
    sb = get_supabase_admin()
    t = sb.table("teams").select("id, nombre, plan").eq("id", team).limit(1).execute().data
    t = t[0] if t else {"id": team, "nombre": None, "plan": None}
    miembros = sb.table("users").select("rol").eq("team_id", team).eq("activo", True).execute().data or []
    counts = {"admin": 0, "closer": 0, "setter": 0}
    for m in miembros:
        if m["rol"] in counts:
            counts[m["rol"]] += 1
    return {**t, "counts": counts, "total": len(miembros)}


# ── Listar miembros (solo admin) ─────────────────────────────────────────────
@router.get("/members")
def listar_members(user: dict = Depends(require_admin)) -> list[dict]:
    sb = get_supabase_admin()
    res = (
        sb.table("users")
        .select("id, nombre, email, rol, activo, created_at, fathom_email")
        .eq("team_id", user["team_id"])
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


# ── Crear miembro (solo admin) ───────────────────────────────────────────────
@router.post("/members")
def crear_member(body: MemberCreate, user: dict = Depends(require_admin)) -> dict:
    if body.rol not in ROLES_INTERNOS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Usá: {', '.join(sorted(ROLES_INTERNOS))}")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    sb = get_supabase_admin()
    email = body.email.lower()
    existe = sb.table("users").select("id").eq("email", email).limit(1).execute().data
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    row = {
        "team_id": user["team_id"],
        "email": email,
        "password_hash": hash_password(body.password),
        "nombre": body.nombre,
        "rol": body.rol,
        "activo": True,
        "is_demo": bool(user.get("is_demo")),
    }
    created = sb.table("users").insert(row).execute().data[0]
    return {"id": created["id"], "email": created["email"], "nombre": created["nombre"],
            "rol": created["rol"], "activo": created["activo"]}


# ── Editar / desactivar miembro (solo admin, mismo workspace) ────────────────
@router.patch("/members/{member_id}")
def editar_member(member_id: str, body: MemberUpdate, user: dict = Depends(require_admin)) -> dict:
    sb = get_supabase_admin()
    target = (
        sb.table("users").select("id, team_id, rol")
        .eq("id", member_id).eq("team_id", user["team_id"]).limit(1).execute().data
    )
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu workspace")

    updates: dict = {}
    if body.nombre is not None:
        updates["nombre"] = body.nombre
    if body.rol is not None:
        if body.rol not in ROLES_INTERNOS:
            raise HTTPException(status_code=400, detail="Rol inválido")
        updates["rol"] = body.rol
    if body.activo is not None:
        # No permitir que el admin se desactive a sí mismo (se quedaría afuera).
        if body.activo is False and member_id == user["id"]:
            raise HTTPException(status_code=400, detail="No podés desactivarte a vos mismo")
        updates["activo"] = body.activo
    if body.password is not None:
        if len(body.password) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        updates["password_hash"] = hash_password(body.password)

    if not updates:
        raise HTTPException(status_code=400, detail="Nada para actualizar")

    sb.table("users").update(updates).eq("id", member_id).execute()
    row = sb.table("users").select("id, nombre, email, rol, activo").eq("id", member_id).limit(1).execute().data[0]
    return row


# ── Código de vinculación con Telegram (setters) ─────────────────────────────
# Sin caracteres ambiguos (0/O, 1/I) para dictarlo o copiarlo sin errores.
_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _nuevo_codigo() -> str:
    return "SMQ-" + "".join(secrets.choice(_ALFABETO) for _ in range(6))


@router.post("/members/{member_id}/telegram-code")
def generar_codigo_telegram(member_id: str, user: dict = Depends(require_admin)) -> dict:
    """Genera (o regenera) el código para que el setter vincule su Telegram.

    Regenerar invalida el anterior y desvincula el chat previo — útil si el setter
    cambió de teléfono o el código se filtró.
    """
    sb = get_supabase_admin()
    target = (
        sb.table("users").select("id, rol, nombre")
        .eq("id", member_id).eq("team_id", user["team_id"]).limit(1).execute().data
    )
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu workspace")
    if target[0]["rol"] != "setter":
        raise HTTPException(status_code=400, detail="Solo los setters se vinculan con Telegram")

    # Reintentar por si choca con el índice único (muy improbable).
    for _ in range(5):
        code = _nuevo_codigo()
        if not sb.table("users").select("id").eq("telegram_link_code", code).limit(1).execute().data:
            break
    sb.table("users").update(
        {"telegram_link_code": code, "telegram_user_id": None}
    ).eq("id", member_id).execute()
    return {"telegram_link_code": code}


@router.get("/members/{member_id}/telegram")
def estado_telegram(member_id: str, user: dict = Depends(require_admin)) -> dict:
    """Estado de vinculación de un setter: si ya vinculó y el código pendiente."""
    sb = get_supabase_admin()
    target = (
        sb.table("users").select("telegram_user_id, telegram_link_code")
        .eq("id", member_id).eq("team_id", user["team_id"]).limit(1).execute().data
    )
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu workspace")
    t = target[0]
    return {
        "vinculado": t.get("telegram_user_id") is not None,
        "telegram_link_code": t.get("telegram_link_code"),
    }


# ── Fathom (ingesta de llamadas de closers) ──────────────────────────────────
@router.get("/fathom")
def fathom_info(user: dict = Depends(require_admin)) -> dict:
    """Devuelve el token del workspace para armar la URL del webhook de Fathom.

    Genera el token de forma perezosa si el workspace no lo tenía.
    """
    sb = get_supabase_admin()
    team = user["team_id"]
    row = sb.table("teams").select("fathom_token").eq("id", team).limit(1).execute().data
    token = row[0].get("fathom_token") if row else None
    if not token:
        token = secrets.token_hex(12)
        sb.table("teams").update({"fathom_token": token}).eq("id", team).execute()
    return {"fathom_token": token, "webhook_path": f"/api/fathom/webhook?token={token}"}


@router.patch("/members/{member_id}/fathom-email")
def set_fathom_email(member_id: str, body: FathomEmail, user: dict = Depends(require_admin)) -> dict:
    """Setea (o limpia) el email de Fathom con el que se atribuyen las llamadas de un closer."""
    sb = get_supabase_admin()
    target = (
        sb.table("users").select("id, rol")
        .eq("id", member_id).eq("team_id", user["team_id"]).limit(1).execute().data
    )
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu workspace")
    if target[0]["rol"] != "closer":
        raise HTTPException(status_code=400, detail="Solo los closers se atribuyen con Fathom")
    valor = (body.fathom_email or "").strip().lower() or None
    sb.table("users").update({"fathom_email": valor}).eq("id", member_id).execute()
    return {"fathom_email": valor}
