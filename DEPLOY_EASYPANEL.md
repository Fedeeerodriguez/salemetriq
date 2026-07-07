# Deploy de SALEMETRIQ en EasyPanel (desde GitHub)

Se despliega como **2 servicios** dentro de un mismo proyecto, ambos desde el
repo `Fedeeerodriguez/salemetriq` (rama `main`):

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  web  (frontend, nginx :80) │  /api  │  api  (backend FastAPI :8000) │
│  Vite build + proxy /api ───┼───────▶│  uvicorn                      │
│  ← dominio público          │ interno│  ← sin dominio público        │
└─────────────────────────────┘        └──────────────────────────────┘
                                                     │
                                             Supabase (cloud)
```

- El navegador solo habla con **web** → nginx proxea `/api` al backend por red
  interna. **No hay CORS** (mismo origen).
- La base es **Supabase cloud** (ya tiene las tablas, migraciones y datos demo).
  No hay que provisionar DB.

---

## 0. Requisitos

- El repo ya está en GitHub (`main`) con los `Dockerfile` de `backend/` y `frontend/`.
- Tener a mano las claves (las mismas de tu `backend/.env` local):
  `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
  `ANTHROPIC_API_KEY`, `JWT_SECRET`.
- En EasyPanel: conectar tu cuenta de GitHub (Settings → GitHub) para poder
  elegir el repo.

Generá un `JWT_SECRET` nuevo para producción:
```bash
openssl rand -hex 32
```

---

## 1. Crear el proyecto

EasyPanel → **Create Project** → nombre: `salemetriq`.

> El nombre del proyecto importa: el host interno de cada servicio queda como
> `<proyecto>_<servicio>`. Con proyecto `salemetriq` y servicio `api`, el backend
> es alcanzable en `http://salemetriq_api:8000` (ya es el default del frontend).

---

## 2. Servicio `api` (backend)

Create Service → **App** → nombre: `api`.

**Source**
- Source: **GitHub** → repo `Fedeeerodriguez/salemetriq`, branch `main`
- **Path / Build context: `/backend`**  ← clave (el Dockerfile copia relativo a esa carpeta)

**Build**
- Type: **Dockerfile**
- File: `Dockerfile`  (relativo al Path `/backend`)

**Environment** (pestaña Environment del servicio) — pegá:
```
SUPABASE_URL=https://ftyapmfywdruivtvdoio.supabase.co
SUPABASE_ANON_KEY=<tu anon key>
SUPABASE_SERVICE_ROLE_KEY=<tu service_role key>
ANTHROPIC_API_KEY=<tu api key>
ANTHROPIC_MODEL=claude-sonnet-5
JWT_SECRET=<el que generaste con openssl>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
INGEST_INTERNAL_KEY=<inventá una clave larga para el webhook de Fathom>
CORS_ORIGINS=https://<tu-dominio-web>
# opcional (solo si usás embeddings/OpenAI)
OPENAI_API_KEY=
```

**Network / Ports**
- Puerto interno: `8000`
- **No** le asignes dominio público (queda interno). *(Opcional: si querés ver
  `/docs`, agregale un dominio y entrá a `https://.../docs`.)*

Deploy.

---

## 3. Servicio `web` (frontend)

Create Service → **App** → nombre: `web`.

**Source**
- Source: **GitHub** → mismo repo, branch `main`
- **Path / Build context: `/frontend`**

**Build**
- Type: **Dockerfile**
- File: `Dockerfile`

**Environment**
```
BACKEND_URL=http://salemetriq_api:8000
```
> Es el host interno del servicio `api`. Formato: `http://<proyecto>_<servicio>:8000`.
> Si nombraste distinto el proyecto/servicio, ajustá acá. (Si no lográs resolver el
> host interno, alternativa: dale un dominio al `api` y poné acá esa URL pública.)

**Network / Ports**
- Puerto interno: `80`
- **Domains**: agregá tu dominio (ej. `salemetriq.tudominio.com`) → EasyPanel
  emite HTTPS (Let's Encrypt) automáticamente.

Deploy.

---

## 4. Verificar

1. Abrí `https://<tu-dominio-web>` → carga el login.
2. Entrá con el usuario demo: `demo@salemetriq.com` / `Demo2026!` → deberías ver
   la plataforma con datos (misma Supabase).
3. Entrá con el admin real → verás producción vacía (correcto).
4. Si algo no carga: **Logs** del servicio `web` (errores de nginx/proxy) y del
   `api` (errores de FastAPI/Supabase).

---

## 5. Webhook de Fathom (ingesta automática del closer)

Apuntá Fathom (u tu automatización) a:
```
POST https://<tu-dominio-web>/api/recordings/ingest/fathom
Header:  X-Ingest-Key: <el INGEST_INTERNAL_KEY que pusiste>
```
Pasa por nginx → backend, dispara el auto-análisis IA. Mismo origen, con HTTPS.

---

## 6. Notas

- **Datos**: la Supabase es la misma que en dev. Las migraciones (`db/schema.sql`,
  `002`, `003`) y el seed demo **ya están aplicadas**. Si algún día apuntás a una
  Supabase nueva: corré esos `.sql` y `backend/scripts/seed_demo.py`.
- **Secretos**: `.env` no se sube al repo (gitignored). Las claves viven solo en
  el panel de Environment de EasyPanel.
- **Redeploy**: cada push a `main` → EasyPanel puede redeployar automático (activá
  "Auto Deploy" en cada servicio) o con el botón Deploy.
- **Prueba local del build de prod** (opcional):
  `docker compose -f docker-compose.prod.yml up --build` → `http://localhost:8080`.
