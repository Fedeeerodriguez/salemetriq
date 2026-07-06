-- ============================================================================
-- SALEMETRIQ — Migración 002: call_recordings ("grabaciones de llamadas")
--
-- Tabla genérica multi-proveedor para alojar transcripts traídos de herramientas
-- de grabación de llamadas. Fathom es el primer proveedor, pero el diseño soporta
-- cualquiera (Fireflies, Gong, Otter, tl;dv, Zoom, carga manual, etc.):
--   - `provider`        identifica la herramienta de origen
--   - `external_id`     id de la grabación en esa herramienta
--   - unique(provider, external_id)  → ingesta idempotente por proveedor
--   - `raw` jsonb       guarda el payload crudo, así no se pierde nada
--   - campos normalizados (transcript, participantes, duración…) comunes a todos
-- El análisis IA se guarda en `analysis_runs` con target_tipo = 'call_recording'.
-- ============================================================================

do $$ begin
  create type recording_status as enum ('nuevo', 'analizando', 'analizado', 'error');
exception when duplicate_object then null; end $$;

create table if not exists call_recordings (
  id                  uuid primary key default uuid_generate_v4(),
  provider            text not null default 'fathom',   -- fathom | fireflies | gong | otter | tldv | zoom | manual ...
  external_id         text,                              -- id de la grabación en el proveedor
  title               text,
  recording_url       text,                              -- link al video/audio en el proveedor
  meeting_url         text,                              -- link de la reunión (zoom/meet)
  transcript          text,                              -- texto plano normalizado
  transcript_segments jsonb,                             -- [{speaker, start, end, text}] si el proveedor lo da
  language            text,
  duration_seg        integer,
  recorded_at         timestamptz,
  participants        jsonb,                             -- [{nombre, email, rol}]
  closer_id           uuid references users(id) on delete set null,
  setter_id           uuid references users(id) on delete set null,
  lead_id             uuid references leads(id) on delete set null,
  call_id             uuid references calls(id) on delete set null,  -- link opcional a la call del pipeline
  status              recording_status not null default 'nuevo',
  raw                 jsonb,                             -- payload crudo del proveedor
  ingested_at         timestamptz not null default now()
);

-- Constraint única real (no parcial) para que el upsert por ON CONFLICT funcione.
-- En Postgres los NULL son distintos entre sí → la carga manual sin external_id
-- no genera colisiones.
do $$ begin
  alter table call_recordings add constraint uq_recordings_provider_external
    unique (provider, external_id);
exception when duplicate_object then null; end $$;

create index if not exists idx_recordings_status on call_recordings(status);
create index if not exists idx_recordings_recorded on call_recordings(recorded_at desc);
create index if not exists idx_recordings_closer on call_recordings(closer_id);
create index if not exists idx_recordings_provider on call_recordings(provider);
