"""Configuración cargada desde variables de entorno (.env)."""
import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Fallback solo para no romper el arranque en dev — definir JWT_SECRET en el entorno.
_DEFAULT_JWT_SECRET = "salemetriq_jwt_secret_change_in_production_2026"


class Settings(BaseSettings):
    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    # service_role key — saltea RLS, solo el backend la conoce.
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Anthropic (Analista IA) ───────────────────────────────────────────────
    # Para análisis de llamadas conviene Sonnet (mejor criterio); Haiku es la
    # opción barata (claude-haiku-4-5). Se puede cambiar por env sin tocar código.
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    # ── OpenAI (embeddings del vector store de transcripts) ───────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4.1-mini"

    # ── Ingesta externa ───────────────────────────────────────────────────────
    INGEST_INTERNAL_KEY: str = ""

    # ── Telegram (setters envían su resumen de setting por el bot) ────────────
    # Token del bot de @BotFather. Sin esto, la Fase A queda deshabilitada.
    TELEGRAM_BOT_TOKEN: str = ""
    # Secret que Telegram manda en el header X-Telegram-Bot-Api-Secret-Token
    # al llamar al webhook — evita que cualquiera postee al endpoint.
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # ── Auth (JWT) ────────────────────────────────────────────────────────────
    JWT_SECRET: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 8

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5180,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

if settings.JWT_SECRET == _DEFAULT_JWT_SECRET:
    # El secret por defecto es público (está en el repo): con él, cualquiera puede
    # firmar un JWT de admin/superadmin. No arrancamos con el default salvo que se
    # pida explícitamente para desarrollo (SMQ_ALLOW_DEFAULT_SECRET=1).
    if os.environ.get("SMQ_ALLOW_DEFAULT_SECRET") == "1":
        logger.warning("SEGURIDAD: usando JWT_SECRET por defecto (solo dev). NO usar en producción.")
    else:
        raise RuntimeError(
            "SEGURIDAD: JWT_SECRET no está definido. Definí JWT_SECRET en el entorno "
            "(o SMQ_ALLOW_DEFAULT_SECRET=1 solo para desarrollo local)."
        )
