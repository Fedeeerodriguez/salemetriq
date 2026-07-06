"""Analista IA de llamadas — Claude API (Messages API + tool use).

Recibe el transcript de una grabación y devuelve un análisis estructurado
(score por dimensión, objeciones, sentiment, momentos clave, resumen).

Structured output vía **tool use**: se define una tool con `input_schema` y se
fuerza `tool_choice` a esa tool, de modo que Claude devuelve JSON válido que
valida contra el schema. Compatible con anthropic 0.40.0 (no requiere
`output_config` ni structured outputs nativo).
"""
import json
import logging

import anthropic

from ..config import settings

logger = logging.getLogger(__name__)

# Herramienta que fuerza el formato de salida. Cada campo mapea a lo que
# guardamos en `analysis_runs`.
ANALYSIS_TOOL = {
    "name": "registrar_analisis",
    "description": "Registra el análisis estructurado de una llamada de ventas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score_global": {
                "type": "integer",
                "description": "Puntaje global de la llamada de 0 a 100.",
            },
            "dimensiones": {
                "type": "object",
                "description": "Puntaje 0-100 por etapa de la llamada.",
                "properties": {
                    "apertura": {"type": "integer"},
                    "descubrimiento": {"type": "integer"},
                    "pitch": {"type": "integer"},
                    "objeciones": {"type": "integer"},
                    "cierre": {"type": "integer"},
                },
                "required": ["apertura", "descubrimiento", "pitch", "objeciones", "cierre"],
            },
            "sentiment": {
                "type": "string",
                "enum": ["positivo", "neutral", "negativo"],
                "description": "Sentimiento general del prospecto.",
            },
            "objeciones": {
                "type": "array",
                "description": "Objeciones detectadas.",
                "items": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "description": "Ej: precio, tiempo, autoridad, necesidad."},
                        "momento": {"type": "string", "description": "Cuándo apareció (ej: 'min 22')."},
                        "manejada": {"type": "boolean", "description": "Si el closer la resolvió."},
                        "nota": {"type": "string"},
                    },
                    "required": ["tipo", "manejada"],
                },
            },
            "momentos_clave": {
                "type": "array",
                "description": "Momentos destacados de la llamada.",
                "items": {
                    "type": "object",
                    "properties": {
                        "t": {"type": "string", "description": "Timestamp aproximado."},
                        "label": {"type": "string"},
                    },
                    "required": ["label"],
                },
            },
            "resumen": {"type": "string", "description": "Resumen ejecutivo de 2-3 frases."},
            "recomendaciones": {
                "type": "array",
                "description": "Acciones concretas para mejorar.",
                "items": {"type": "string"},
            },
        },
        "required": ["score_global", "dimensiones", "sentiment", "resumen"],
    },
}

_SYSTEM = (
    "Sos un analista senior de ventas B2B de habla hispana (Argentina). Analizás "
    "transcripts de llamadas de cierre (closers) con criterio, sin adular. Evaluás "
    "apertura, descubrimiento de dolor, pitch, manejo de objeciones y cierre. Sos "
    "concreto y accionable. Respondés SIEMPRE llamando a la tool registrar_analisis."
)


def analizar_transcript(transcript: str, contexto: str | None = None) -> dict:
    """Analiza un transcript y devuelve el dict estructurado del análisis.

    Lanza RuntimeError si no hay ANTHROPIC_API_KEY o si el modelo no devuelve la tool.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY — configurala en backend/.env para analizar.")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = "Analizá la siguiente llamada de ventas.\n"
    if contexto:
        prompt += f"\nContexto: {contexto}\n"
    prompt += f"\n--- TRANSCRIPT ---\n{transcript}\n--- FIN ---"

    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=_SYSTEM,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "registrar_analisis"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in resp.content:
        if block.type == "tool_use" and block.name == "registrar_analisis":
            return block.input  # dict validado contra input_schema

    # No debería pasar con tool_choice forzado.
    logger.error("El modelo no devolvió la tool. stop_reason=%s", resp.stop_reason)
    raise RuntimeError("El modelo no devolvió un análisis estructurado.")
