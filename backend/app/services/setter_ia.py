"""Estructurador IA de resúmenes de setting — Claude API (tool use).

El setter manda por Telegram un resumen libre de cómo le fue con un lead (texto o
voz transcripta). Claude lo convierte en un resumen estructurado: calificación del
lead, si quedó agendado, próximo paso y un resumen limpio. Mismo patrón de
`analista_ia`: se fuerza `tool_choice` sobre una tool para obtener JSON válido.
"""
import logging

import anthropic

from ..config import settings

logger = logging.getLogger(__name__)

SETTER_TOOL = {
    "name": "registrar_resumen_setting",
    "description": "Registra el resumen estructurado de un setting hecho por un setter.",
    "input_schema": {
        "type": "object",
        "properties": {
            "resumen": {
                "type": "string",
                "description": "Resumen ejecutivo y limpio del setting en 2-3 frases.",
            },
            "lead_qualification": {
                "type": "string",
                "enum": ["caliente", "tibio", "frio", "descartado"],
                "description": "Qué tan calificado/listo para cerrar quedó el lead.",
            },
            "agendado": {
                "type": "boolean",
                "description": "Si el setter dejó agendada una llamada de cierre.",
            },
            "proximo_paso": {
                "type": "string",
                "description": "La próxima acción concreta con este lead.",
            },
            "objeciones": {
                "type": "array",
                "description": "Dudas u objeciones que planteó el lead.",
                "items": {"type": "string"},
            },
            "nota_coach": {
                "type": "string",
                "description": "Una sugerencia breve para que el setter mejore el próximo setting.",
            },
        },
        "required": ["resumen", "lead_qualification", "agendado"],
    },
}

_SYSTEM = (
    "Sos un coach de setting/prospección B2B de habla hispana (Argentina). Recibís "
    "el relato libre de un setter sobre cómo le fue con un lead y lo convertís en un "
    "resumen estructurado y accionable. Inferí la calificación del lead y si quedó "
    "agendada una llamada de cierre. Sé fiel a lo que dijo el setter, no inventes datos. "
    "Respondés SIEMPRE llamando a la tool registrar_resumen_setting."
)


def estructurar_resumen(texto: str) -> dict:
    """Devuelve el dict estructurado del resumen de setting.

    Lanza RuntimeError si no hay ANTHROPIC_API_KEY o si el modelo no devuelve la tool.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Falta ANTHROPIC_API_KEY — configurala para estructurar resúmenes.")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1000,
        system=_SYSTEM,
        tools=[SETTER_TOOL],
        tool_choice={"type": "tool", "name": "registrar_resumen_setting"},
        messages=[{"role": "user", "content": f"Relato del setter:\n\n{texto}"}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "registrar_resumen_setting":
            return block.input
    logger.error("El modelo no devolvió la tool. stop_reason=%s", resp.stop_reason)
    raise RuntimeError("El modelo no devolvió un resumen estructurado.")
