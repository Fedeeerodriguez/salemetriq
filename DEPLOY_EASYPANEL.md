# Deploy de IG PROSPECTOR en EasyPanel (desde GitHub)

Se despliega como **2 servicios** dentro de un mismo proyecto, ambos desde el
repo `Fedeeerodriguez/salemetriq`, **rama `scraper-ig`**:

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  web  (frontend, nginx :80) │  /api  │  api  (backend FastAPI :8000) │
│  Vite build + proxy /api ───┼───────▶│  uvicorn                      │
│  ← dominio público          │ interno│  ← sin dominio público        │
└─────────────────────────────┘        └──────────────────────────────┘
                                                     │
                                    Supabase (cloud)  +  Apify (fuente)
```

- El navegador solo habla con **web** → nginx proxea `/api` al backend por red
  interna. **No hay CORS** (mismo origen).
- La base es **Supabase cloud**. Antes de deployar hay que **crear un proyecto
  Supabase nuevo para IG Prospector** y correr `db/schema.sql`.

---

## 0. Requisitos previos

1. **Supabase**: crear un proyecto nuevo (NO reuses el de SALEMETRIQ — tienen
   tablas distintas). En el SQL Editor, pegar y correr **`db/schema.sql`**.
   Copiar de Settings → API: `Project URL`, `anon key` y `service_role key`.
2. **Apify** (opcional pero recomendado): crear cuenta free en apify.com →
   Settings → Integrations → **API token**. Sin token, el backend corre en MODO
   MOCK (perfiles de ejemplo) — sirve para probar el deploy, no para datos reales.
3. **JWT_SECRET** de producción:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
4. En EasyPanel: conectar tu cuenta de GitHub (Settings → GitHub).

---

## 1. Crear el proyecto

EasyPanel → **Create Project** → nombre: `ig-prospector`.

> El nombre importa: el host interno de cada servicio queda como
> `<proyecto>_<servicio>`. Con proyecto `ig-prospector` y servicio `api`, el backend
> es alcanzable en `http://ig-prospector_api:8000` (ya es el default del frontend).

---

## 2. Servicio `api` (backend)

Create Service → **App** → nombre: `api`.

**Source**
- Source: **GitHub** → repo `Fedeeerodriguez/salemetriq`, branch **`scraper-ig`**
- **Path / Build context: `/backend`**  ← clave (el Dockerfile copia relativo a esa carpeta)

**Build**
- Type: **Dockerfile** · File: `Dockerfile`

**Environment** — pegá (completando tus valores):
```
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=<anon key>
SUPABASE_SERVICE_ROLE_KEY=<service_role key>
APIFY_TOKEN=<tu token de Apify>          # vacío = MODO MOCK
APIFY_ACTOR=apify/instagram-scraper
APIFY_MAX_RESULTS=200
ANTHROPIC_API_KEY=<opcional, para clasificador IA>
ANTHROPIC_MODEL=claude-haiku-4-5
JWT_SECRET=<el que generaste>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8
IGP_ENCRYPTION_KEY=<opcional; python -c "import secrets;print(secrets.token_urlsafe(32))">
CORS_ORIGINS=https://<tu-dominio-web>
```

**Network / Ports**
- Puerto interno: `8000`
- **No** le asignes dominio público (queda interno). *(Opcional: dale un dominio
  temporal para ver `/docs`.)*

Deploy.

**Crear el primer admin** (una vez deployado): en el servicio `api` →
**Console/Terminal** de EasyPanel:
```bash
python create_admin.py admin@igprospector.com "TuPasswordFuerte" "Admin"
```
> ⚠️ En producción `SUPABASE_SERVICE_ROLE_KEY` está seteada → **NO** usa el fake
> in-memory; escribe en tu Supabase real.

---

## 3. Servicio `web` (frontend)

Create Service → **App** → nombre: `web`.

**Source**
- Source: **GitHub** → mismo repo, branch **`scraper-ig`**
- **Path / Build context: `/frontend`**

**Build**
- Type: **Dockerfile** · File: `Dockerfile`

**Environment**
```
BACKEND_URL=http://ig-prospector_api:8000
```
> Host interno del servicio `api`. Formato `http://<proyecto>_<servicio>:8000`.
> Si nombraste distinto, ajustá. (Alternativa si no resuelve: dale dominio al `api`
> y poné acá esa URL pública.)

**Network / Ports**
- Puerto interno: `80`
- **Domains**: agregá tu dominio → EasyPanel emite HTTPS (Let's Encrypt) automático.

Deploy.

---

## 4. Verificar

1. Abrí `https://<tu-dominio-web>` → carga el login de IG Prospector.
2. Entrá con el admin que creaste → deberías ver **Buscar / Perfiles / Nichos / Listas**.
3. Creá un nicho, lanzá una búsqueda. Con `APIFY_TOKEN` trae perfiles reales; sin
   token, perfiles MOCK (para validar el deploy).
4. Si algo no carga: **Logs** del servicio `web` (nginx/proxy) y del `api`
   (FastAPI/Supabase/Apify).

---

## 5. Notas

- **Secretos**: `.env` no se sube (gitignored). Las claves viven solo en el panel
  Environment de EasyPanel.
- **Redeploy**: cada push a `scraper-ig` → activá "Auto Deploy" en cada servicio,
  o usá el botón Deploy.
- **Costo Apify**: el plan free (US$5/mes) alcanza para miles de perfiles. El techo
  por búsqueda se controla con `APIFY_MAX_RESULTS` y el campo "Límite" de cada búsqueda.
- **Prueba local del build de prod** (opcional):
  `docker compose -f docker-compose.prod.yml up --build`.
