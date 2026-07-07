"""Adapter de Fathom → call_recordings.

Fathom manda el webhook "new meeting content ready" cuando termina de procesar una
llamada. Formato real (campos top-level), con fallbacks a formas anidadas por si el
payload viene de un intermediario (Zapier/Make/n8n):

{
  "id" / "recording_id",
  "title" / "meeting_title",
  "url", "share_url",
  "recording_start_time", "recording_end_time",
  "scheduled_start_time", "scheduled_end_time",
  "transcript_language",
  "recorded_by": {"name": "...", "email": "..."},
  "calendar_invitees": [{"name": "...", "email": "...", "is_external": true}],
  "transcript": [
     {"speaker": {"display_name": "...", "matched_calendar_invitee_email": "..."},
      "text": "...", "timestamp": "00:01:23"}
  ]
}

`normalizar()` devuelve un dict con las columnas de call_recordings. La atribución
(team + closer) NO se hace acá: la resuelve el webhook con `host_email()`.
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


def _flatten_transcript(payload: dict) -> str | None:
    """Convierte el transcript (array de Fathom o texto plano) en texto legible."""
    # Ya viene plano en algún proveedor/intermediario.
    plano = _get(payload, "transcript.plaintext", "transcript.text", "transcript_plaintext")
    if isinstance(plano, str) and plano.strip():
        return plano

    items = _get(payload, "transcript", "transcript.segments", "segments")
    if isinstance(items, str):
        return items or None
    if not isinstance(items, list):
        return None

    lineas: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        speaker = (
            _get(it, "speaker.display_name", "speaker", "speaker_name", "display_name")
            or "Interlocutor"
        )
        texto = _get(it, "text", "spoken_text", "content", default="")
        if texto:
            lineas.append(f"{speaker}: {texto}")
    return "\n".join(lineas) or None


def _participants(payload: dict) -> list | None:
    inv = _get(payload, "calendar_invitees", "participants", "meeting.participants")
    if not isinstance(inv, list):
        return None
    out = []
    for p in inv:
        if isinstance(p, dict):
            out.append({
                "nombre": _get(p, "name", "display_name"),
                "email": _get(p, "email", "matched_calendar_invitee_email"),
                "externo": _get(p, "is_external"),
            })
    return out or None


def host_email(payload: dict) -> str | None:
    """Email de quien grabó la llamada (para atribuir el closer)."""
    email = _get(
        payload,
        "recorded_by.email", "recorded_by.user_email",
        "host.email", "owner.email", "user.email", "recorded_by_email",
    )
    return email.lower() if isinstance(email, str) else None


def invitee_emails(payload: dict) -> list[str]:
    """Emails de los invitados — fallback de atribución si el host no matchea."""
    parts = _participants(payload) or []
    return [p["email"].lower() for p in parts if p.get("email")]


def normalizar(payload: dict) -> dict:
    return {
        "external_id": _get(payload, "id", "recording.id", "recording_id"),
        "title": _get(payload, "title", "meeting_title", "meeting.title", "topic",
                      default="Llamada sin título"),
        "recording_url": _get(payload, "share_url", "url", "recording.share_url", "recording.url"),
        "meeting_url": _get(payload, "meeting_url", "meeting.url", "join_url"),
        "transcript": _flatten_transcript(payload),
        "transcript_segments": _get(payload, "transcript", "transcript.segments", "segments")
            if isinstance(_get(payload, "transcript", "segments"), list) else None,
        "language": _get(payload, "transcript_language", "transcript.language", "language", default="es"),
        "duration_seg": _get(payload, "duration_seconds", "meeting.duration_seconds", "duration"),
        "recorded_at": _get(payload, "recording_start_time", "meeting.started_at",
                            "started_at", "recorded_at", "created_at"),
        "participants": _participants(payload),
    }
