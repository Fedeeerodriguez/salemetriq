"""Auth: hashing de passwords, emisión/verificación de JWT y dependencia de usuario.

Los usuarios viven en la tabla `users` de Supabase (columnas: id, email,
password_hash, nombre, rol, activo). En Fase 0 el login valida contra esa tabla
usando el cliente admin (service_role).
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from ..config import settings
from .supabase_client import get_supabase_admin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ── Passwords ─────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(user_id: str, rol: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "rol": rol,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# ── Dependencia de usuario actual ─────────────────────────────────────────────
def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    cred_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o sesión expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_error
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise cred_error

    user_id = payload.get("sub")
    if not user_id:
        raise cred_error

    sb = get_supabase_admin()
    res = sb.table("users").select("id, email, nombre, rol, activo").eq("id", user_id).limit(1).execute()
    user = res.data[0] if res.data else None
    if not user or not user.get("activo", True):
        raise cred_error
    return user


def require_roles(*roles: str):
    """Factory de dependencia: exige que el usuario tenga alguno de los roles."""

    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user.get("rol") not in roles:
            raise HTTPException(status_code=403, detail="No autorizado para esta acción")
        return user

    return _check
