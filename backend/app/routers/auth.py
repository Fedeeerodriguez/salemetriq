"""Router de autenticación — login con email/password → JWT + aceptar invitación."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    nombre: str | None = None
    rol: str
    team_id: str | None = None
    is_superadmin: bool = False
    workspace: str | None = None
    brand_color: str | None = None


def _workspace(sb, team_id: str | None) -> dict:
    if not team_id:
        return {"nombre": None, "brand_color": None}
    row = sb.table("teams").select("nombre, brand_color").eq("id", team_id).limit(1).execute().data
    return row[0] if row else {"nombre": None, "brand_color": None}


def _user_out(sb, user: dict) -> "UserOut":
    ws = _workspace(sb, user.get("team_id"))
    return UserOut(
        id=user["id"], email=user["email"], nombre=user.get("nombre"), rol=user["rol"],
        team_id=user.get("team_id"), is_superadmin=bool(user.get("is_superadmin")),
        workspace=ws.get("nombre"), brand_color=ws.get("brand_color"),
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AcceptInviteRequest(BaseModel):
    token: str
    password: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    sb = get_supabase_admin()
    res = (
        sb.table("users")
        .select("id, email, nombre, rol, password_hash, activo, team_id, is_superadmin")
        .eq("email", body.email.lower())
        .limit(1)
        .execute()
    )
    user = res.data[0] if res.data else None
    if not user or not user.get("activo", True):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if not verify_password(body.password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = create_access_token(user["id"], user["rol"])
    return LoginResponse(access_token=token, user=_user_out(sb, user))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    return _user_out(get_supabase_admin(), user)


class UpdateMeRequest(BaseModel):
    nombre: str | None = None
    password_actual: str | None = None
    password_nueva: str | None = None


@router.patch("/me", response_model=UserOut)
def actualizar_me(body: UpdateMeRequest, user: dict = Depends(get_current_user)) -> UserOut:
    """El usuario edita su propio perfil: nombre y/o contraseña."""
    sb = get_supabase_admin()
    updates: dict = {}

    if body.nombre is not None:
        nombre = body.nombre.strip()
        if not nombre:
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
        updates["nombre"] = nombre

    if body.password_nueva:
        if len(body.password_nueva) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        row = sb.table("users").select("password_hash").eq("id", user["id"]).limit(1).execute().data
        actual_hash = (row[0].get("password_hash") if row else "") or ""
        if not verify_password(body.password_actual or "", actual_hash):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
        updates["password_hash"] = hash_password(body.password_nueva)

    if not updates:
        raise HTTPException(status_code=400, detail="No hay cambios para guardar")

    sb.table("users").update(updates).eq("id", user["id"]).execute()
    fresh = (
        sb.table("users").select("id, email, nombre, rol, team_id, is_superadmin")
        .eq("id", user["id"]).limit(1).execute().data
    )
    return _user_out(sb, fresh[0] if fresh else {**user, **updates})


# ── Invitaciones (alta sin password) ─────────────────────────────────────────
def _invite_valido(row: dict) -> bool:
    exp = row.get("invite_expires")
    if not exp:
        return True  # sin vencimiento explícito
    try:
        dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
        if dt.tzinfo is None:  # naive → asumir UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False  # fail-closed: si no se puede parsear, tratar como inválida


@router.get("/invite/{token}")
def ver_invitacion(token: str) -> dict:
    """Datos para la pantalla de 'definir contraseña' (pública, valida el token)."""
    sb = get_supabase_admin()
    res = (
        sb.table("users").select("id, email, nombre, rol, team_id, invite_expires")
        .eq("invite_token", token).limit(1).execute().data
    )
    row = res[0] if res else None
    if not row or not _invite_valido(row):
        raise HTTPException(status_code=404, detail="Invitación inválida o vencida")
    return {
        "email": row["email"],
        "nombre": row.get("nombre"),
        "rol": row["rol"],
        "workspace": _workspace(sb, row.get("team_id")).get("nombre"),
    }


@router.post("/accept-invite", response_model=LoginResponse)
def aceptar_invitacion(body: AcceptInviteRequest) -> LoginResponse:
    """El invitado define su contraseña, queda activo y se loguea."""
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    sb = get_supabase_admin()
    res = (
        sb.table("users").select("id, email, nombre, rol, team_id, is_superadmin, invite_expires")
        .eq("invite_token", body.token).limit(1).execute().data
    )
    user = res[0] if res else None
    if not user or not _invite_valido(user):
        raise HTTPException(status_code=404, detail="Invitación inválida o vencida")

    sb.table("users").update({
        "password_hash": hash_password(body.password),
        "activo": True,
        "invite_token": None,
        "invite_expires": None,
    }).eq("id", user["id"]).execute()

    token = create_access_token(user["id"], user["rol"])
    return LoginResponse(access_token=token, user=_user_out(sb, user))
