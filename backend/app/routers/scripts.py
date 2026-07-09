"""Router de generación de scripts — guiones de venta a medida del método.

`GET  /api/scripts/tipos`    → catálogo de tipos de guion disponibles.
`POST /api/scripts/generar`  → genera un guion estructurado (tipo + contexto).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..services.auth import get_current_user
from ..services.script_ia import TIPOS, generar_script

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


class GenerarRequest(BaseModel):
    tipo: str
    contexto: str | None = None


@router.get("/tipos")
def tipos(_: dict = Depends(get_current_user)) -> list[dict]:
    return [{"value": k, "descripcion": v} for k, v in TIPOS.items()]


@router.post("/generar")
def generar(body: GenerarRequest, _: dict = Depends(get_current_user)) -> dict:
    if not body.tipo or body.tipo not in TIPOS:
        raise HTTPException(status_code=400, detail="Tipo de script inválido.")
    try:
        return generar_script(body.tipo, body.contexto)
    except RuntimeError as e:
        # Falta API key o el modelo no devolvió estructura → 503 (servicio no disponible).
        raise HTTPException(status_code=503, detail=str(e))
