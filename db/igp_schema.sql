-- ============================================================================
-- IG PROSPECTOR — Schema AISLADO dentro del proyecto Supabase de SALEMETRIQ.
--
-- Vive en su propia "carpeta" (schema Postgres `igp`), separado del `public` de
-- SALEMETRIQ. Así NO colisiona con la tabla users / enum user_rol de la otra app,
-- aunque compartan la misma base.
--
-- Aplicar con: SMQ_DB_PASS='...' .venv/Scripts/python scripts/apply_sql.py ../db/igp_schema.sql
-- Idempotente. Todo objeto queda calificado con el prefijo igp.*
-- ============================================================================

create schema if not exists igp;

-- ── Enums (dentro de igp) ────────────────────────────────────────────────────
do $$ begin
  create type igp.user_rol as enum ('admin', 'operador');
exception when duplicate_object then null; end $$;

do $$ begin
  create type igp.job_angulo as enum ('hashtag', 'keyword', 'followers', 'ubicacion');
exception when duplicate_object then null; end $$;

do $$ begin
  create type igp.job_estado as enum ('pendiente', 'corriendo', 'ok', 'error');
exception when duplicate_object then null; end $$;

do $$ begin
  create type igp.contacto_estado as enum ('nuevo', 'contactado', 'respondio', 'descartado');
exception when duplicate_object then null; end $$;

-- ── updated_at automático (propio de igp) ────────────────────────────────────
create or replace function igp.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- ── users ────────────────────────────────────────────────────────────────────
create table if not exists igp.users (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  password_hash text not null,
  nombre        text,
  rol           igp.user_rol not null default 'operador',
  activo        boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_igp_users_rol on igp.users(rol);
drop trigger if exists trg_igp_users_updated on igp.users;
create trigger trg_igp_users_updated before update on igp.users
  for each row execute function igp.set_updated_at();

-- ── nichos ───────────────────────────────────────────────────────────────────
create table if not exists igp.nichos (
  id              uuid primary key default gen_random_uuid(),
  nombre          text not null,
  descripcion     text,
  keywords        text[] not null default '{}',
  hashtags        text[] not null default '{}',
  cuentas_semilla text[] not null default '{}',
  usa_ia          boolean not null default false,
  created_by      uuid references igp.users(id) on delete set null,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists idx_igp_nichos_nombre on igp.nichos(nombre);
drop trigger if exists trg_igp_nichos_updated on igp.nichos;
create trigger trg_igp_nichos_updated before update on igp.nichos
  for each row execute function igp.set_updated_at();

-- ── scrape_jobs ──────────────────────────────────────────────────────────────
create table if not exists igp.scrape_jobs (
  id                uuid primary key default gen_random_uuid(),
  nicho_id          uuid references igp.nichos(id) on delete set null,
  angulo            igp.job_angulo not null,
  query             text not null,
  filtros           jsonb not null default '{}',
  estado            igp.job_estado not null default 'pendiente',
  total_encontrados integer not null default 0,
  total_nuevos      integer not null default 0,
  error_msg         text,
  created_by        uuid references igp.users(id) on delete set null,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index if not exists idx_igp_jobs_estado on igp.scrape_jobs(estado);
create index if not exists idx_igp_jobs_created on igp.scrape_jobs(created_at desc);
drop trigger if exists trg_igp_jobs_updated on igp.scrape_jobs;
create trigger trg_igp_jobs_updated before update on igp.scrape_jobs
  for each row execute function igp.set_updated_at();

-- ── ig_profiles ──────────────────────────────────────────────────────────────
create table if not exists igp.ig_profiles (
  username         text primary key,
  full_name        text,
  bio              text,
  followers        integer,
  following        integer,
  posts            integer,
  is_business      boolean,
  category         text,
  external_url     text,
  email_publico    text,
  telefono_publico text,
  profile_pic_url  text,
  ig_url           text,
  nicho_id         uuid references igp.nichos(id) on delete set null,
  score_nicho      integer not null default 0,
  ia_veredicto     text,
  ia_motivo        text,
  scraped_at       timestamptz not null default now(),
  created_at       timestamptz not null default now()
);
create index if not exists idx_igp_profiles_nicho on igp.ig_profiles(nicho_id);
create index if not exists idx_igp_profiles_score on igp.ig_profiles(score_nicho desc);
create index if not exists idx_igp_profiles_followers on igp.ig_profiles(followers desc);

-- ── listas ───────────────────────────────────────────────────────────────────
create table if not exists igp.listas (
  id          uuid primary key default gen_random_uuid(),
  nombre      text not null,
  descripcion text,
  owner       uuid references igp.users(id) on delete set null,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
drop trigger if exists trg_igp_listas_updated on igp.listas;
create trigger trg_igp_listas_updated before update on igp.listas
  for each row execute function igp.set_updated_at();

-- ── lista_perfiles (N:M) ─────────────────────────────────────────────────────
create table if not exists igp.lista_perfiles (
  id              uuid primary key default gen_random_uuid(),
  lista_id        uuid not null references igp.listas(id) on delete cascade,
  username        text not null references igp.ig_profiles(username) on delete cascade,
  estado_contacto igp.contacto_estado not null default 'nuevo',
  nota            text,
  created_at      timestamptz not null default now(),
  unique (lista_id, username)
);
create index if not exists idx_igp_lp_lista on igp.lista_perfiles(lista_id);
create index if not exists idx_igp_lp_username on igp.lista_perfiles(username);

-- ============================================================================
-- Permisos para PostgREST / service_role (el backend accede con service_role).
-- Sin estos grants, el cliente Supabase no puede leer/escribir en el schema igp.
-- ============================================================================
grant usage on schema igp to anon, authenticated, service_role;
grant all privileges on all tables    in schema igp to service_role;
grant all privileges on all sequences in schema igp to service_role;
grant all privileges on all functions in schema igp to service_role;
alter default privileges in schema igp grant all on tables    to service_role;
alter default privileges in schema igp grant all on sequences to service_role;
