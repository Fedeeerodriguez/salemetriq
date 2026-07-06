"""Adapters de proveedores de grabación de llamadas.

Cada adapter normaliza el payload de un proveedor (Fathom, Fireflies, Gong, …)
al formato común de la tabla `call_recordings`. Para sumar un proveedor nuevo:
crear un módulo con una función `normalizar(payload: dict) -> dict` y registrarlo
en ADAPTERS.
"""
from . import fathom

# provider → función normalizadora
ADAPTERS = {
    "fathom": fathom.normalizar,
}


def normalizar(provider: str, payload: dict) -> dict:
    fn = ADAPTERS.get(provider)
    if not fn:
        raise ValueError(f"Proveedor no soportado: {provider}")
    row = fn(payload)
    row["provider"] = provider
    row["raw"] = payload
    return row
