-- ============================================================================
-- SALEMETRIQ — Schema inicial (Supabase / Postgres)
-- Sales telemetry: equipos, usuarios, llamadas de closers, resúmenes de setters,
-- pipeline de leads/deals, análisis IA y métricas agregadas.
--
-- Ejecutar en el SQL Editor de Supabase (o vía `apply_migration`).
-- Idempotente: usa IF NOT EXISTS y enums con guardas.
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists vector;      -- embeddings de transcripts (Fase 3)

-- ── Enums ────────────────────────────────────────────────────────────────────
do $$ begin
  create type user_rol as enum ('admin', 'manager', 'closer', 'setter');
exception when duplicate_object then null; end $$;

do $$ begin
  create type call_outcome as enum ('cerro', 'no_cerro', 'seguimiento', 'no_show');
exception when duplicate_object then null; end $$;

do $$ begin
  create type summary_tipo as enum ('texto', 'audio');
exception when duplicate_object then null; end $$;

-- ── Función utilitaria: updated_at automático ────────────────────────────────
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- ── teams ────────────────────────────────────────────────────────────────────
create table if not exists teams (
  id          uuid primary key default uuid_generate_v4(),
  nombre      text not null,
  created_at  timestamptz not null default now()
);

-- ── users ────────────────────────────────────────────────────────────────────
-- Auth propia (JWT del backend). password_hash con bcrypt.
create table if not exists users (
  id            uuid primary key default uuid_generate_v4(),
  team_id       uuid references teams(id) on delete set null,
  email         text unique not null,
  password_hash text not null,
  nombre        text,
  rol           user_rol not null default 'closer',
  activo        boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_users_rol on users(rol);
create index if not exists idx_users_team on users(team_id);
drop trigger if exists trg_users_updated on users;
create trigger trg_users_updated before update on users
  for each row execute function set_updated_at();

-- ── leads (pipeline) ─────────────────────────────────────────────────────────
create table if not exists leads (
  id           uuid primary key default uuid_generate_v4(),
  team_id      uuid references teams(id) on delete set null,
  nombre       text,
  contacto     text,                       -- email / teléfono
  origen       text,                        -- fuente del lead
  setter_id    uuid references users(id) on delete set null,
  closer_id    uuid references users(id) on delete set null,
  estado       text default 'nuevo',        -- nuevo | agendado | en_proceso | ganado | perdido
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
create index if not exists idx_leads_setter on leads(setter_id);
create index if not exists idx_leads_closer on leads(closer_id);
drop trigger if exists trg_leads_updated on leads;
create trigger trg_leads_updated before update on leads
  for each row execute function set_updated_at();

-- ── calls (llamadas de closers) ──────────────────────────────────────────────
create table if not exists calls (
  id            uuid primary key default uuid_generate_v4(),
  closer_id     uuid references users(id) on delete set null,
  lead_id       uuid references leads(id) on delete set null,
  fecha         timestamptz not null default now(),
  duracion_seg  integer,
  outcome       call_outcome,
  deal_value    numeric(14,2) default 0,
  transcript    text not null,
  created_at    timestamptz not null default now()
);
create index if not exists idx_calls_closer on calls(closer_id);
create index if not exists idx_calls_fecha on calls(fecha desc);
create index if not exists idx_calls_outcome on calls(outcome);

-- ── setter_summaries (resúmenes de setters, audio/texto) ─────────────────────
create table if not exists setter_summaries (
  id                  uuid primary key default uuid_generate_v4(),
  setter_id           uuid references users(id) on delete set null,
  lead_id             uuid references leads(id) on delete set null,
  fecha               timestamptz not null default now(),
  tipo                summary_tipo not null default 'texto',
  texto               text,
  audio_url           text,
  lead_qualification  text,                 -- calificación cualitativa del lead
  agendado            boolean default false,
  created_at          timestamptz not null default now()
);
create index if not exists idx_summaries_setter on setter_summaries(setter_id);
create index if not exists idx_summaries_fecha on setter_summaries(fecha desc);

-- ── analysis_runs (salida del analista IA — Fase 3) ──────────────────────────
-- Guarda el resultado del análisis de una call o de un summary.
create table if not exists analysis_runs (
  id            uuid primary key default uuid_generate_v4(),
  target_tipo   text not null,              -- 'call' | 'setter_summary'
  target_id     uuid not null,
  modelo        text,                        -- modelo IA usado
  score         numeric(5,2),                -- 0..100
  sentiment     text,
  objeciones    jsonb,                       -- lista de objeciones detectadas
  tags          text[],
  resumen       text,
  raw           jsonb,                       -- salida cruda del modelo
  created_at    timestamptz not null default now()
);
create index if not exists idx_analysis_target on analysis_runs(target_tipo, target_id);

-- ── transcript_chunks (vector store para búsqueda semántica — Fase 3) ────────
-- text-embedding-3-small → 1536 dims.
create table if not exists transcript_chunks (
  id          uuid primary key default uuid_generate_v4(),
  call_id     uuid references calls(id) on delete cascade,
  chunk       text not null,
  embedding   vector(1536),
  created_at  timestamptz not null default now()
);
create index if not exists idx_chunks_call on transcript_chunks(call_id);
-- Índice ANN (crear cuando haya volumen de datos):
-- create index on transcript_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- ── metrics_daily (agregados pre-calculados — Fase 3) ────────────────────────
create table if not exists metrics_daily (
  id            uuid primary key default uuid_generate_v4(),
  fecha         date not null,
  user_id       uuid references users(id) on delete cascade,
  rol           user_rol,
  llamadas      integer default 0,
  cerradas      integer default 0,
  close_rate    numeric(5,2) default 0,
  revenue       numeric(14,2) default 0,
  agendados     integer default 0,
  set_rate      numeric(5,2) default 0,
  score_prom    numeric(5,2),
  created_at    timestamptz not null default now(),
  unique (fecha, user_id)
);
create index if not exists idx_metrics_fecha on metrics_daily(fecha desc);

-- ============================================================================
-- RLS — se activa en un archivo aparte (db/rls.sql) una vez definido cómo se
-- mapean los usuarios de la app a auth.uid() de Supabase. Por ahora el backend
-- accede con service_role (saltea RLS).
-- ============================================================================
