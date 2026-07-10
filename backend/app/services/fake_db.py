"""Fake de Supabase EN MEMORIA — solo para desarrollo/testing local.

Implementa el subconjunto de la API de supabase-py que usa la app
(`table().select().eq().execute()`, insert/update/upsert/delete, filtros, order,
range, count) contra listas de dicts en memoria. NO persiste entre reinicios.

Se activa automáticamente cuando NO hay SUPABASE_SERVICE_ROLE_KEY configurada, así
el flujo completo (login → buscar en MODO MOCK → perfiles → listas → export) se
puede probar sin un proyecto Supabase real. En producción, con la key, se usa el
cliente real y este módulo ni se toca.
"""
import uuid
from datetime import datetime, timezone

# Almacén global: nombre_tabla -> lista de filas (dicts).
_STORE: dict[str, list[dict]] = {}
# Tablas cuya PK NO es 'id' (no se les autogenera id).
_PK_USERNAME = {"ig_profiles"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Result:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


def _match_or(row: dict, expr: str) -> bool:
    """Parsea el subconjunto de PostgREST or_() que usa la app."""
    for term in expr.split(","):
        term = term.strip()
        if term.endswith(".not.is.null"):
            col = term[: -len(".not.is.null")]
            if row.get(col) is not None:
                return True
        elif ".ilike." in term:
            col, _, pat = term.partition(".ilike.")
            needle = pat.strip("%").lower()
            val = (row.get(col) or "")
            if needle in str(val).lower():
                return True
    return False


class _Query:
    def __init__(self, table: str):
        self.table = table
        self.rows = _STORE.setdefault(table, [])
        self._filters = []          # lista de callables row->bool
        self._mode = "select"
        self._payload = None
        self._cols = "*"
        self._count = None
        self._order = None          # (col, desc)
        self._range = None          # (a, b)
        self._limit = None
        self._on_conflict = None
        self._ignore_dup = False

    # ── builders ──────────────────────────────────────────────────────────────
    def select(self, cols="*", count=None):
        self._mode = "select"; self._cols = cols; self._count = count; return self

    def insert(self, payload):
        self._mode = "insert"; self._payload = payload; return self

    def update(self, payload):
        self._mode = "update"; self._payload = payload; return self

    def upsert(self, payload, on_conflict=None, ignore_duplicates=False):
        self._mode = "upsert"; self._payload = payload
        self._on_conflict = on_conflict; self._ignore_dup = ignore_duplicates; return self

    def delete(self):
        self._mode = "delete"; return self

    def eq(self, col, val):
        self._filters.append(lambda r: r.get(col) == val); return self

    def in_(self, col, vals):
        s = set(vals)
        self._filters.append(lambda r: r.get(col) in s); return self

    def gte(self, col, val):
        self._filters.append(lambda r: r.get(col) is not None and r.get(col) >= val); return self

    def lte(self, col, val):
        self._filters.append(lambda r: r.get(col) is not None and r.get(col) <= val); return self

    def or_(self, expr):
        self._filters.append(lambda r: _match_or(r, expr)); return self

    def order(self, col, desc=False):
        self._order = (col, desc); return self

    def range(self, a, b):
        self._range = (a, b); return self

    def limit(self, n):
        self._limit = n; return self

    # ── ejecución ─────────────────────────────────────────────────────────────
    def _filtered(self):
        return [r for r in self.rows if all(f(r) for f in self._filters)]

    def _conflict_keys(self):
        return [k.strip() for k in (self._on_conflict or "id").split(",")]

    def execute(self):
        if self._mode == "select":
            data = self._filtered()
            total = len(data)
            if self._order:
                col, desc = self._order
                data = sorted(data, key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)
            if self._range:
                a, b = self._range
                data = data[a:b + 1]
            elif self._limit is not None:
                data = data[: self._limit]
            return _Result([dict(r) for r in data], count=total if self._count else None)

        if self._mode == "insert":
            filas = self._payload if isinstance(self._payload, list) else [self._payload]
            creadas = [self._nueva(dict(f)) for f in filas]
            self.rows.extend(creadas)
            return _Result([dict(r) for r in creadas])

        if self._mode == "update":
            afectadas = self._filtered()
            for r in afectadas:
                r.update(self._payload)
                r["updated_at"] = _now()
            return _Result([dict(r) for r in afectadas])

        if self._mode == "upsert":
            filas = self._payload if isinstance(self._payload, list) else [self._payload]
            keys = self._conflict_keys()
            out = []
            for f in filas:
                existente = next((r for r in self.rows if all(r.get(k) == f.get(k) for k in keys)), None)
                if existente:
                    if self._ignore_dup:
                        out.append(existente); continue
                    existente.update(f); existente["updated_at"] = _now()
                    out.append(existente)
                else:
                    nueva = self._nueva(dict(f))
                    self.rows.append(nueva); out.append(nueva)
            return _Result([dict(r) for r in out])

        if self._mode == "delete":
            afectadas = self._filtered()
            quedan = [r for r in self.rows if r not in afectadas]
            self.rows[:] = quedan
            return _Result([])

        return _Result([])

    def _nueva(self, fila: dict) -> dict:
        if self.table not in _PK_USERNAME and "id" not in fila:
            fila["id"] = str(uuid.uuid4())
        fila.setdefault("created_at", _now())
        fila.setdefault("updated_at", _now())
        return fila


class FakeSupabase:
    def table(self, name: str) -> _Query:
        return _Query(name)


def seed(hash_password) -> None:
    """Siembra un admin de dev y un nicho de ejemplo (si están vacíos)."""
    users = _STORE.setdefault("users", [])
    if not users:
        users.append({
            "id": str(uuid.uuid4()),
            "email": "admin@igprospector.com",
            "password_hash": hash_password("Admin1234"),
            "nombre": "Admin Dev",
            "rol": "admin",
            "activo": True,
            "created_at": _now(), "updated_at": _now(),
        })
    nichos = _STORE.setdefault("nichos", [])
    if not nichos:
        nichos.append({
            "id": str(uuid.uuid4()),
            "nombre": "Médicos",
            "descripcion": "Profesionales de la salud (nicho de ejemplo)",
            "keywords": ["medico", "médico", "dr", "clínica", "cardiólogo", "salud"],
            "hashtags": ["medicos", "medicina", "cardiologia"],
            "cuentas_semilla": ["sociedadcardiologia"],
            "usa_ia": True,
            "created_by": None,
            "created_at": _now(), "updated_at": _now(),
        })
