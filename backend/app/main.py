"""FastAPI app del backend de SALEMETRIQ — sales telemetry.

Ingesta de transcripts (closers) y resúmenes (setters), motor de métricas y
analista IA sobre Supabase.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth as auth_router
from .routers import closers, setters, ingesta, metricas, grabaciones, calls, users, workspace, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SALEMETRIQ — Backend",
    version="0.1.0",
    description="Sales telemetry: ingesta de llamadas, métricas y analista IA sobre Supabase.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Ingest-Key"],
)

app.include_router(auth_router.router)
app.include_router(closers.router)
app.include_router(setters.router)
app.include_router(ingesta.router)
app.include_router(metricas.router)
app.include_router(grabaciones.router)
app.include_router(calls.router)
app.include_router(users.router)
app.include_router(workspace.router)
app.include_router(admin.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "salemetriq-backend", "status": "running"}


@app.on_event("startup")
def _on_startup() -> None:
    logger.info("SALEMETRIQ backend arrancado — CORS origins: %s", settings.cors_origins_list)
