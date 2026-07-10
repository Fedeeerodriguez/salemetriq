"""Cifrado simétrico para credenciales de terceros en reposo (Fernet/AES-128).

Se usa para guardar, cifradas en la DB, credenciales sensibles (ej. cookies de
sesión de IG si algún día se suma el collector por login). La clave sale de
IGP_ENCRYPTION_KEY; si no está, se deriva de JWT_SECRET (para no romper dev,
aunque conviene definir una propia en producción).
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings


def _fernet() -> Fernet:
    raw = settings.IGP_ENCRYPTION_KEY or settings.JWT_SECRET
    # Fernet requiere 32 bytes url-safe base64; derivamos con SHA-256.
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return Fernet(key)


def encrypt(texto: str) -> str:
    return _fernet().encrypt(texto.encode()).decode()


def decrypt(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        return None
