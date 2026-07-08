"""Analista IA de llamadas — Claude API (Messages API + tool use).

Evalúa el transcript de una llamada de cierre contra el MÉTODO DE CLOSING del
cliente (ver sales_framework.RUBRICA): puntúa cada etapa, detecta qué técnicas
específicas usó/omitió y devuelve coaching accionable con frases mejores.

Structured output vía tool use (compatible con anthropic 0.40.0).
"""
import logging

import anthropic

from ..config import settings
from .sales_framework import RUBRICA

logger = logging.getLogger(__name__)

# Etapas del framework — son las claves de `dimensiones` (score 0-100 c/u).
ETAPAS = ["cualificacion", "visualizacion", "consecuencia", "pitch", "objeciones", "cierre"]

ANALYSIS_TOOL = {
    "name": "registrar_analisis",
    "description": "Registra el análisis estructurado de una llamada de cierre contra el método.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score_global": {"type": "integer", "description": "Puntaje global 0-100 de la ejecución del método."},
            "dimensiones": {
                "type": "object",
                "description": "Puntaje 0-100 por etapa del método.",
                "properties": {e: {"type": "integer"} for e in ETAPAS},
                "required": ETAPAS,
            },
            "etapas": {
                "type": "array",
                "description": "Detalle por etapa del método.",
                "items": {
                    "type": "object",
                    "properties": {
                        "etapa": {"type": "string", "enum": ETAPAS},
                        "score": {"type": "integer"},
                        "hizo_bien": {"type": "string", "description": "Qué ejecutó bien de esta etapa (concreto)."},
                        "falto": {"type": "string", "description": "Qué técnica del método faltó o se ejecutó mal."},
                        "evidencia": {"type": "string", "description": "Cita breve del transcript que lo respalda."},
                    },
                    "required": ["etapa", "score", "falto"],
                },
            },
            "checklist": {
                "type": "object",
                "description": "Técnicas específicas del método: true si se usó bien.",
                "properties": {
                    "uso_especificamente": {"type": "boolean"},
                    "outcome_definido": {"type": "boolean"},
                    "urgencia_tiempo": {"type": "boolean"},
                    "motivo_emocional_profundo": {"type": "boolean"},
                    "tres_creencias": {"type": "boolean"},
                    "lenguaje_cuando_yo_te_lleve": {"type": "boolean"},
                    "profundizo_visualizacion": {"type": "boolean"},
                    "reality_check": {"type": "boolean"},
                    "como_te_harias_sentir": {"type": "boolean"},
                    "pregunta_del_control": {"type": "boolean"},
                    "micro_compromiso_pre_pitch": {"type": "boolean"},
                    "pitch_que_porque_como": {"type": "boolean"},
                    "objeciones_orden_correcto": {"type": "boolean"},
                    "asumio_cierre": {"type": "boolean"},
                    "tie_down": {"type": "boolean"},
                },
            },
            "sentiment": {"type": "string", "enum": ["positivo", "neutral", "negativo"]},
            "objeciones": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "description": "finanzas | logistica | miedo | otra"},
                        "momento": {"type": "string"},
                        "manejada": {"type": "boolean"},
                        "nota": {"type": "string"},
                    },
                    "required": ["tipo", "manejada"],
                },
            },
            "fortalezas": {"type": "array", "items": {"type": "string"}},
            "mejoras": {
                "type": "array",
                "description": "Mejoras accionables priorizadas, ancladas al método.",
                "items": {
                    "type": "object",
                    "properties": {
                        "etapa": {"type": "string", "enum": ETAPAS},
                        "accion": {"type": "string", "description": "Qué debería hacer distinto."},
                        "prioridad": {"type": "string", "enum": ["alta", "media", "baja"]},
                        "ejemplo": {"type": "string", "description": "Frase concreta mejor, en el estilo del método."},
                    },
                    "required": ["accion", "prioridad"],
                },
            },
            "proxima_accion": {"type": "string", "description": "La UNA cosa del método a trabajar antes de la próxima llamada."},
            "resumen": {"type": "string", "description": "Resumen ejecutivo de 2-3 frases."},
        },
        "required": ["score_global", "dimensiones", "etapas", "checklist", "sentiment",
                     "resumen", "mejoras", "proxima_accion"],
    },
}

_SYSTEM = (
    "Sos un coach senior de closing de habla hispana (Argentina). Evaluás transcripts "
    "de llamadas de cierre ESTRICTAMENTE contra el método que sigue abajo. No inventes "
    "un criterio propio: puntuá cada etapa por qué tan fiel fue la ejecución al método, "
    "detectá qué técnicas específicas usó u omitió (checklist), y para cada mejora dá una "
    "frase concreta mejor en el estilo del método (usá los wordtracks del método). Sé honesto "
    "y específico, sin adular; si una etapa no ocurrió, ponela en score bajo y marcá qué faltó. "
    "Respondés SIEMPRE llamando a la tool registrar_analisis.\n\n"
    "=== MÉTODO ===\n" + RUBRICA
)


def analizar_transcript(transcript: str, contexto: str | None = None) -> dict:
    """Analiza un transcript contra el método y devuelve el dict estructurado.

    Lanza RuntimeError si no hay ANTHROPIC_API_KEY o si el modelo no devuelve la tool.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY — configurala en backend/.env para analizar.")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = "Analizá la siguiente llamada de cierre contra el método.\n"
    if contexto:
        prompt += f"\nContexto: {contexto}\n"
    prompt += f"\n--- TRANSCRIPT ---\n{transcript}\n--- FIN ---"

    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=5000,  # el análisis por etapas + mejoras con ejemplos es extenso
        system=_SYSTEM,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "registrar_analisis"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in resp.content:
        if block.type == "tool_use" and block.name == "registrar_analisis":
            return block.input

    logger.error("El modelo no devolvió la tool. stop_reason=%s", resp.stop_reason)
    raise RuntimeError("El modelo no devolvió un análisis estructurado.")


def narrativa_coaching(datos: str, alcance: str) -> str | None:
    """Genera un resumen de coaching (texto) a partir de agregados ya calculados.

    `alcance` = "closer" | "equipo". Devuelve None si no hay API key.
    """
    if not settings.ANTHROPIC_API_KEY:
        return None
    if alcance == "equipo":
        pedido = (
            "Escribí un diagnóstico BREVE (máx 6 viñetas) para el líder comercial: dónde está "
            "fallando el equipo según el método, qué patrón se repite, y las 2-3 palancas de "
            "mejora más importantes. Concreto y accionable, anclado al método."
        )
    else:
        pedido = (
            "Escribí un resumen de coaching BREVE (máx 5 viñetas) para este closer: sus fortalezas, "
            "sus 2-3 fugas recurrentes según el método, y la próxima cosa a trabajar. Directo, sin adular."
        )
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        resp = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=700,
            system="Sos un coach de closing. Evaluás contra este método:\n\n" + RUBRICA,
            messages=[{"role": "user", "content": f"{pedido}\n\nDatos agregados:\n{datos}"}],
        )
        partes = [b.text for b in resp.content if b.type == "text"]
        return "\n".join(partes).strip() or None
    except Exception:  # noqa: BLE001 — la narrativa es opcional, no debe romper el endpoint
        logger.exception("Fallo generando narrativa de coaching")
        return None
