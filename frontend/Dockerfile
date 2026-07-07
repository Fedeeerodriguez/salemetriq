# ── SALEMETRIQ — Frontend (Vite build → nginx) ──────────────────────────────
# Build context: frontend/    ·    Puerto expuesto: 80
#
# nginx sirve el SPA y proxea /api → backend (mismo origen, sin CORS).
# La URL del backend se resuelve por envsubst desde la variable BACKEND_URL.

# Stage 1 — build del bundle
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2 — servir con nginx
FROM nginx:alpine
# Host interno del servicio backend en EasyPanel. Sobreescribible por env.
# Formato habitual: http://<proyecto>_<servicio>:8000
ENV BACKEND_URL=http://salemetriq_api:8000
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
# La imagen nginx corre envsubst sobre /etc/nginx/templates/*.template al arrancar
# (reemplaza ${BACKEND_URL}) y luego levanta nginx.
