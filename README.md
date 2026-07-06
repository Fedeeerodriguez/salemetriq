# SALEMETRIQ

**Sales telemetry / conversation intelligence.** Trackea automáticamente las
métricas de un equipo de ventas: analiza **transcripts de llamadas** (closers) y
**resúmenes por audio y texto** (setters), los guarda en una base de datos y los
convierte en métricas comparables.

> *La voz se vuelve dato.*

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite 6 + Tailwind 3 · supabase-js, axios, react-router, recharts, lucide-react |
| Backend | FastAPI + uvicorn · supabase-py, pydantic-settings, PyJWT + bcrypt, anthropic + openai |
| DB | Supabase (Postgres 17) + pgvector · RLS |
| Infra | docker-compose, GitHub Action keep-alive |

## Estructura

```
salemetriq/
├── backend/          # FastAPI  (app/config, main, routers/, services/)
├── frontend/         # React + Vite + Tailwind (identidad SALEMETRIQ)
├── db/               # schema.sql y migraciones SQL
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
cp .env.example .env                                # completar keys
.venv/Scripts/uvicorn app.main:app --reload --port 8000
# Crear el primer admin:
.venv/Scripts/python create_admin.py admin@salemetriq.com MiPassword "Admin"
```
API: http://localhost:8000 — Swagger: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env                                # completar VITE_SUPABASE_*
npm run dev
```
App: http://localhost:5180 (Vite proxya `/api` → `http://localhost:8000`)

## Modelo de datos

`teams` · `users` (roles: admin/manager/closer/setter) · `leads` · `calls`
(transcripts de closers) · `setter_summaries` (audio/texto) · `analysis_runs`
(salida IA) · `transcript_chunks` (vector store) · `metrics_daily` (agregados).

## Roadmap

- **Fase 0 — Andamiaje** ✅ esqueleto full-stack que levanta en local.
- **Fase 1** — Auth + gestión de usuarios/equipos.
- **Fase 2** — Ingesta de transcripts (closers) y resúmenes (setters).
- **Fase 3** — Motor de métricas + analista IA (scoring, objeciones, sentiment).
- **Fase 4** — Dashboard completo con la identidad visual de SALEMETRIQ.
