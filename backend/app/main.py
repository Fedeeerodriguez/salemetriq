"""FastAPI app del backend de IG PROSPECTOR.

Buscar perfiles de Instagram por nicho (fuente: Apify), deduplicarlos, puntuarlos
por afinidad y agruparlos en listas para outreach manual. NO envía ni reacciona.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth as auth_router
from .routers import busqueda, listas, nichos, perfiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IG Prospector — Backend",
    version="0.1.0",
    description="Búsqueda de perfiles de Instagram por nicho → listas para outreach manual.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router.router)
app.include_router(nichos.router)
app.include_router(busqueda.router)
app.include_router(perfiles.router)
app.include_router(listas.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ig-prospector-backend", "status": "running"}


@app.on_event("startup")
def _on_startup() -> None:
    fuente = "Apify" if settings.APIFY_TOKEN else "MOCK (sin APIFY_TOKEN)"
    from .services import supabase_client
    if supabase_client.USE_FAKE:
        from .services.auth import hash_password
        from .services.fake_db import seed
        seed(hash_password)
        logger.info("DEV MODE — admin sembrado: admin@igprospector.com / Admin1234")
    logger.info("IG Prospector backend arrancado — fuente de datos: %s", fuente)
