"""Configuración cargada desde variables de entorno (.env)."""
import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Fallback solo para no romper el arranque en dev — definir JWT_SECRET en el entorno.
_DEFAULT_JWT_SECRET = "igprospector_jwt_secret_change_in_production_2026"


class Settings(BaseSettings):
    # ── Supabase (base de datos) ──────────────────────────────────────────────
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    # service_role key — saltea RLS, solo el backend la conoce.
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Apify (fuente de scraping — plan free, sin arriesgar tu cuenta) ────────
    APIFY_TOKEN: str = ""
    # Actor por defecto para búsquedas por hashtag/keyword/followers.
    APIFY_ACTOR: str = "apify/instagram-scraper"
    # Techo duro de resultados por búsqueda (para no quemar el crédito free).
    APIFY_MAX_RESULTS: int = 200

    # ── Anthropic (clasificador de nicho — Fase 4, opcional) ──────────────────
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-haiku-4-5"

    # ── Cifrado de credenciales de terceros en reposo (Fernet) ────────────────
    # Si no se define, se deriva de JWT_SECRET (menos ideal, pero funcional).
    IGP_ENCRYPTION_KEY: str = ""

    # ── Auth (JWT) ────────────────────────────────────────────────────────────
    JWT_SECRET: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 8

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5182,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

if settings.JWT_SECRET == _DEFAULT_JWT_SECRET:
    # El secret por defecto es público (está en el repo): con él cualquiera puede
    # firmar un JWT de admin. No arrancamos con el default salvo que se pida
    # explícitamente para desarrollo (IGP_ALLOW_DEFAULT_SECRET=1).
    if os.environ.get("IGP_ALLOW_DEFAULT_SECRET") == "1":
        logger.warning("SEGURIDAD: usando JWT_SECRET por defecto (solo dev). NO usar en producción.")
    else:
        raise RuntimeError(
            "SEGURIDAD: JWT_SECRET no está definido. Definí JWT_SECRET en el entorno "
            "(o IGP_ALLOW_DEFAULT_SECRET=1 solo para desarrollo local)."
        )
