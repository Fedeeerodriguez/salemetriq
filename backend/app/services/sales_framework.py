"""Framework de closing (el 'cerebro' del análisis de llamadas).

Rúbrica destilada del método comercial del cliente. El analista IA evalúa cada
llamada contra ESTE marco: cada etapa, sus técnicas específicas y el orden.

Si el método cambia, se edita este texto y el análisis se actualiza solo (se
inyecta en el system prompt de analista_ia).
"""

RUBRICA = """\
MÉTODO DE CLOSING (evaluá la llamada contra esto, etapa por etapa).

Principio rector: la persuasión ocurre en la cabeza del prospecto, no en la boca
del closer. El closer PREGUNTA y GUÍA; el prospecto se autoconvence. Todo se
conecta de vuelta al OUTCOME definido en Cualificación. Ventas = servicio.

ETAPA 1 — CUALIFICACIÓN (Estado Actual / Descubrimiento)
Objetivo: definir el resultado deseado (outcome) y abrir la brecha entre dónde
está y dónde quiere estar. Técnicas clave:
- Preguntar el outcome "ESPECÍFICAMENTE" (la palabra importa; sin ella la respuesta es genérica).
- Mapear el método actual y por cuánto tiempo lo hace (construye urgencia con su propia respuesta).
- Pregunta de "pequeños cambios" para darle salida al ego (no ponerse a la defensiva).
- Separar "cuánto hace que usás ESE método" de "cuánto hace que VOS intentás lograr esto".
- "¿Por qué SENTÍS que...?" (emocional, no "por qué pensás").
- Cerrar con el motivo emocional profundo (por qué es importante AHORA), quitándole las respuestas obvias.
Excelente = el prospecto verbaliza que su método no funciona, que lleva mucho sin resultado y que le importa de verdad.

ETAPA 2 — VISUALIZACIÓN (Deseo)
Objetivo: que VEA, SIENTA y CREA el resultado. Deben quedar en pie 3 creencias:
posibilidad ("¿es posible?"), capacidad ("¿soy capaz YO?"), merecimiento ("¿me lo merezco?").
Si falla una, no hay venta. Técnicas:
- Lenguaje "cuando YO te lleve" (el closer toma la responsabilidad/liderazgo del resultado), no "cuando vos logres".
- No CONTARLE la visión: hacer que la CONSTRUYA él. Profundizar más allá de las respuestas de relleno ("sería increíble") hasta el núcleo emocional real (ej: presencia con los hijos), con "¿a qué te referís?", "¿qué te permitiría eso?".
- Enmarcar como "cuando esto suceda", no "si sucediera".
Excelente = deseo emocional concreto y personal, con las 3 creencias intactas.

ETAPA 3 — CONSECUENCIA DE LA INACCIÓN (Miedo)
Objetivo: hacer tangible el costo de no actuar y trasladar la responsabilidad al prospecto.
REGLA CRÍTICA: nunca bajar de golpe del pico de Visualización al fondo de Miedo.
Primero un REALITY CHECK (escalón intermedio): confrontar con respeto la realidad
ACTUAL ("hoy claramente no tenés las habilidades / estás lejos, ¿no?") y esperar un "sí".
Recién ahí bajar. Técnicas:
- "¿Cómo te HARÍAS SENTIR...?" (no "cómo se vería" — evita que se escape a "eso no me va a pasar").
- Palabra "conformar" ("¿te vas a conformar con que esto sea tu realidad de nuevo?") → casi siempre "no" → inmediatamente "¿por qué no?".
- Pregunta central de la llamada: "¿QUIÉN tiene el control / es el responsable de que logres esto?" → llevar hasta que diga "YO".
- "¿Qué decisiones necesitás tomar hoy?" (sugestiva, antes del pitch).
- Reframes ante "yo igual lo voy a lograr": espejo emocional (tiempo, versión actual vs futura), sin contradecir de frente.
Tono: más bajo, calmado, serio. No soltar la etapa hasta que el miedo esté presente.

ETAPA 4 — PITCH (Solución)
Objetivo: organizar/materializar la visión que el prospecto ya empezó a construir.
Técnicas:
- Micro-compromiso ANTES del pitch ("¿querés que te muestre cómo sería el plan?") → el pitch es pedido, no impuesto.
- Presentar por pilares/mecanismos, cada uno con QUÉ / POR QUÉ (personalizado a SU outcome y dolor) / CÓMO (implementación).
- Conectar cada mecanismo al dolor y deseo revelados. No abrumar con detalle técnico.
- Asumir el cierre. No pausar después de decir el precio: fluir directo al próximo paso.

ETAPA 5 — OBJECIONES
Principios: el trabajo pesado se hizo en descubrimiento (muchas objeciones = descubrimiento flojo).
El manejo se hace POR el prospecto, no contra él. El closer debe ser decisivo para que ellos lo sean.
ORDEN OBLIGATORIO para resolver: 1) FINANZAS  2) LOGÍSTICA (tiempo/socios)  3) MIEDO.
Técnicas: sacar el dinero de la ecuación para aislar el deseo real; reframes (auto-sabotaje,
ingenio, manejo de riesgo vs certeza, analogía del gimnasio/auto); confrontar creencias limitantes
con emoción (no lógica); tie-down "dibujar una línea en la arena".

CIERRE / TIE-DOWNS (transversal)
Tie-downs de compromiso ("¿es el momento de comprometerte de verdad?") después de etapas clave;
obligatorio después del pitch. Cierre = coherencia entre problema, responsabilidad asumida y plan.

CHECKLIST DE CIERRE (deben estar presentes): Brecha, Deseo, Miedo, Preparación (se siente capaz), Urgencia.
"""
