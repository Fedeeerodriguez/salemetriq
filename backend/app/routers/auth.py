"""Router de autenticación — login con email/password → JWT."""
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


def _user_out(user: dict) -> "UserOut":
    return UserOut(
        id=user["id"], email=user["email"],
        nombre=user.get("nombre"), rol=user["rol"],
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    sb = get_supabase_admin()
    res = (
        sb.table("users")
        .select("id, email, nombre, rol, password_hash, activo")
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
    return LoginResponse(access_token=token, user=_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


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
    return _user_out({**user, **updates})
