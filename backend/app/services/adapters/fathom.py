"""Adapter de Fathom → call_recordings.

Fathom entrega la grabación + transcript vía webhook/API. Los nombres de campo
pueden variar según la versión del webhook, así que leemos con varios fallbacks
y guardamos el payload completo en `raw` (en el nivel superior, ver __init__).

Payload típico (simplificado):
{
  "recording": {"id": "...", "url": "...", "share_url": "..."},
  "meeting":   {"title": "...", "started_at": "...", "duration_seconds": 1234,
                "url": "https://zoom.us/..."},
  "transcript": {"plaintext": "...", "language": "es",
                 "segments": [{"speaker": "...", "start": 0, "end": 5, "text": "..."}]},
  "participants": [{"name": "...", "email": "..."}]
}
"""
from typing import Any


def _get(d: dict, *keys, default=None) -> Any:
    """Devuelve el primer valor no nulo entre varias rutas 'a.b.c'."""
    for key in keys:
        cur: Any = d
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return default


def normalizar(payload: dict) -> dict:
    segments = _get(payload, "transcript.segments", "segments", default=None)

    return {
        "external_id": _get(payload, "recording.id", "id", "recording_id"),
        "title": _get(payload, "meeting.title", "title", "topic", default="Llamada sin título"),
        "recording_url": _get(payload, "recording.share_url", "recording.url", "share_url", "url"),
        "meeting_url": _get(payload, "meeting.url", "meeting_url"),
        "transcript": _get(payload, "transcript.plaintext", "transcript.text", "transcript", "text"),
        "transcript_segments": segments,
        "language": _get(payload, "transcript.language", "language", default="es"),
        "duration_seg": _get(payload, "meeting.duration_seconds", "duration_seconds", "duration"),
        "recorded_at": _get(payload, "meeting.started_at", "started_at", "recorded_at", "created_at"),
        "participants": _get(payload, "participants", "meeting.participants"),
    }
