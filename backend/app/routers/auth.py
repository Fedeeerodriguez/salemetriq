"""Router de autenticación — login con email/password → JWT."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from ..services.auth import (
    create_access_token,
    get_current_user,
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


def _workspace_name(sb, team_id: str | None) -> str | None:
    if not team_id:
        return None
    row = sb.table("teams").select("nombre").eq("id", team_id).limit(1).execute().data
    return row[0]["nombre"] if row else None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


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
    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=user["id"], email=user["email"], nombre=user.get("nombre"), rol=user["rol"],
            team_id=user.get("team_id"), is_superadmin=bool(user.get("is_superadmin")),
            workspace=_workspace_name(sb, user.get("team_id")),
        ),
    )


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    sb = get_supabase_admin()
    return UserOut(
        id=user["id"], email=user["email"], nombre=user.get("nombre"), rol=user["rol"],
        team_id=user.get("team_id"), is_superadmin=bool(user.get("is_superadmin")),
        workspace=_workspace_name(sb, user.get("team_id")),
    )
