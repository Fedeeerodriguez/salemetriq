# IG PROSPECTOR

**Prospección de Instagram por nicho.** Buscás un nicho (ej. *"médicos"*) por
hashtag, keyword, seguidores de una cuenta semilla o ubicación, y la app trae
perfiles públicos reales, los **deduplica**, los **puntúa por afinidad al nicho** y
los agrupa en **listas** para contactarlos después **a mano**.

> **Solo lista y exporta. NO envía mensajes ni reacciona.**

## Fuente de datos y seguridad

La fuente es **Apify** (plan free, US$5 crédito/mes sin tarjeta): **no usa tu cuenta
de Instagram**, así que no hay riesgo de ban ni mantenimiento de anti-bloqueo. El
collector es **enchufable**: se puede sumar otra fuente (login+Playwright,
instaloader) sin tocar el resto de la app.

> Sin `APIFY_TOKEN`, el backend corre en **MODO MOCK** (perfiles de ejemplo) para
> poder probar todo el flujo end-to-end sin gastar crédito.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite 6 + Tailwind 3 · axios, react-router, lucide-react |
| Backend | FastAPI + uvicorn · supabase-py, pydantic-settings, PyJWT + bcrypt, httpx |
| DB | Supabase (Postgres) |
| Fuente | Apify (Instagram) vía httpx — collector enchufable |
| Infra | docker-compose / EasyPanel (backend uvicorn + frontend nginx) |

## Estructura

```
ig-prospector/
├── backend/          # FastAPI (app/config, main, routers/, services/collector*, scoring, dedup, ig_jobs)
├── frontend/         # React + Vite + Tailwind (tema obsidiana violeta→cian)
├── db/               # schema.sql (Supabase)
└── docker-compose.yml
```

## Puesta en marcha (dev)

### 1. Base de datos (Supabase)
1. Crear un proyecto en Supabase.
2. Correr `db/schema.sql` en el SQL Editor.
3. Copiar `SUPABASE_URL`, `anon key` y `service_role key`.

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows
cp .env.example .env                                # completar keys (Supabase, JWT_SECRET, APIFY_TOKEN)
.venv/Scripts/uvicorn app.main:app --reload --port 8000
# Crear el primer usuario admin:
.venv/Scripts/python create_admin.py admin@igprospector.com MiPassword "Admin"
```
API: http://localhost:8000 — Swagger: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5182 (Vite proxya `/api` → `http://localhost:8000`)

## Modelo de datos

`users` (roles: admin/operador) · `nichos` (keywords + hashtags + cuentas semilla)
· `scrape_jobs` (búsquedas encoladas, corren en background) · `ig_profiles`
(dedup por username, con `score_nicho`) · `listas` · `lista_perfiles` (N:M con
estado de follow-up manual: nuevo/contactado/respondió/descartado).

## Flujo

1. **Nichos** — definís el nicho y sus señales.
2. **Buscar** — elegís nicho + ángulo (hashtag/keyword/seguidores/ubicación) + filtros → se encola un job que corre en background.
3. **Perfiles** — tabla filtrable y puntuada; seleccionás y mandás a una lista.
4. **Listas** — gestionás el estado de contacto y **exportás a CSV** (UTF-8-BOM).

## Roadmap

- **Fase 1 — Backend base** ✅ auth (JWT) + modelo + Supabase.
- **Fase 2 — Motor de búsqueda** ✅ collector Apify + scoring + dedup + jobs.
- **Fase 3 — Frontend** ✅ nichos, buscar, perfiles, listas, export CSV.
- **Fase 4 — Clasificador IA** (opcional) — Claude marca sí/no/dudoso por bio.
- **Fase 5 — Deploy** — Dockerfiles + EasyPanel (2 servicios).
