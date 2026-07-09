"""Generador de scripts de venta — Claude API (Messages API + tool use).

Genera guiones a medida ANCLADOS al método de closing del cliente
(sales_framework: RUBRICA + SCRIPTING_GUIA). Comparte el mismo "cerebro" que el
analista, así lo que se genera y lo que se evalúa hablan el mismo idioma.

Structured output vía tool use (compatible con anthropic 0.40.0).
"""
import logging

import anthropic

from ..config import settings
from .sales_framework import RUBRICA, SCRIPTING_GUIA

logger = logging.getLogger(__name__)

# Tipos de script disponibles (value → descripción para el modelo).
TIPOS = {
    "llamada_completa": "Llamada de cierre completa, de punta a punta (todas las etapas del método).",
    "cualificacion": "Descubrimiento / cualificación: definir el resultado deseado y abrir la brecha.",
    "visualizacion": "Fase de deseo: que el prospecto vea, sienta y crea el resultado.",
    "consecuencia": "Consecuencia de la inacción / miedo, con reality check.",
    "pitch": "Pitch de la oferta por pilares (QUÉ / POR QUÉ / CÓMO).",
    "objeciones": "Manejo de objeciones en orden (finanzas → logística → miedo).",
    "objecion_precio": "Manejo específico de la objeción de precio.",
    "cierre_urgencia": "Cierre por urgencia con tie-downs de compromiso.",
    "apertura_frio": "Apertura en frío / primer contacto (setting).",
    "no_show": "Recuperación de no-show y reagendado.",
}

SCRIPT_TOOL = {
    "name": "registrar_script",
    "description": "Registra un guion de venta estructurado y anclado al método.",
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string", "description": "Título del guion."},
            "objetivo": {"type": "string", "description": "Qué logra este guion (1-2 frases)."},
            "secciones": {
                "type": "array",
                "description": "Pasos/etapas del guion, en orden.",
                "items": {
                    "type": "object",
                    "properties": {
                        "etapa": {"type": "string", "description": "Nombre del paso (ej: 'Cualificación', 'Reality check')."},
                        "objetivo": {"type": "string", "description": "Micro-objetivo de este paso."},
                        "lineas": {
                            "type": "array",
                            "description": "Las frases/preguntas EXACTAS a decir, con placeholders entre [CORCHETES].",
                            "items": {"type": "string"},
                        },
                        "tips": {
                            "type": "array",
                            "description": "Claves de ejecución: qué escuchar, cómo adaptar, señales.",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["etapa", "lineas"],
                },
            },
            "objeciones": {
                "type": "array",
                "description": "Respuestas a objeciones frecuentes para este contexto (si aplica).",
                "items": {
                    "type": "object",
                    "properties": {
                        "objecion": {"type": "string"},
                        "tipo": {"type": "string", "description": "finanzas | logistica | miedo"},
                        "respuesta": {"type": "string", "description": "Wordtrack para manejarla, anclado al método."},
                    },
                    "required": ["objecion", "respuesta"],
                },
            },
            "checklist": {
                "type": "array",
                "description": "Qué tiene que quedar cubierto al terminar (ej: Brecha, Deseo, Miedo, Urgencia).",
                "items": {"type": "string"},
            },
            "notas": {"type": "string", "description": "Notas de ejecución o advertencias del método."},
        },
        "required": ["titulo", "objetivo", "secciones"],
    },
}

_SYSTEM = (
    "Sos un director de ventas de habla hispana (Argentina) experto en closing high-ticket. "
    "Escribís guiones (scripts) para closers/setters ESTRICTAMENTE en el estilo y la estructura "
    "del método que sigue abajo: mismas etapas, mismos wordtracks, mismo orden de objeciones. "
    "Las líneas del guion tienen que sonar naturales y humanas (no de robot), usar placeholders "
    "entre [CORCHETES] para lo específico del contexto, y respetar las reglas del método (ej: reality "
    "check antes del miedo; objeciones en orden finanzas→logística→miedo; asumir el cierre). "
    "Adaptá el guion al tipo pedido y al contexto del usuario. Respondés SIEMPRE llamando a la tool "
    "registrar_script.\n\n"
    "=== MÉTODO (rúbrica) ===\n" + RUBRICA + "\n\n"
    "=== GUÍA DE SCRIPTING (wordtracks y plantillas) ===\n" + SCRIPTING_GUIA
)


def generar_script(tipo: str, contexto: str | None = None) -> dict:
    """Genera un guion estructurado del `tipo` pedido, ajustado al `contexto`.

    Lanza RuntimeError si no hay ANTHROPIC_API_KEY o si el modelo no devuelve la tool.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY — configurala en backend/.env para generar scripts.")

    desc_tipo = TIPOS.get(tipo, tipo)
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"Generá un guion de tipo: {desc_tipo}\n"
    if contexto and contexto.strip():
        prompt += f"\nContexto del negocio / prospecto / oferta:\n{contexto.strip()}\n"
    else:
        prompt += "\nNo se dio contexto específico: usá placeholders genéricos entre [CORCHETES].\n"
    prompt += "\nDevolvé el guion llamando a registrar_script, con líneas listas para leer."

    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4000,
        system=_SYSTEM,
        tools=[SCRIPT_TOOL],
        tool_choice={"type": "tool", "name": "registrar_script"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in resp.content:
        if block.type == "tool_use" and block.name == "registrar_script":
            return block.input

    logger.error("El modelo no devolvió la tool de script. stop_reason=%s", resp.stop_reason)
    raise RuntimeError("El modelo no devolvió un guion estructurado.")
