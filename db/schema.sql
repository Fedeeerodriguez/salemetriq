-- ============================================================================
-- IG PROSPECTOR — Schema inicial (Supabase / Postgres)
-- Buscar perfiles de Instagram por NICHO de forma masiva, deduplicarlos,
-- puntuarlos por afinidad al nicho y agruparlos en LISTAS para outreach manual.
--
-- La app NO envía mensajes ni reacciona: solo enlista, clasifica y exporta.
--
-- Ejecutar en el SQL Editor de Supabase (o vía `apply_migration`).
-- Idempotente: usa IF NOT EXISTS y enums con guardas.
-- ============================================================================

create extension if not exists "uuid-ossp";

-- ── Enums ────────────────────────────────────────────────────────────────────
do $$ begin
  create type user_rol as enum ('admin', 'operador');
exception when duplicate_object then null; end $$;

do $$ begin
  create type job_angulo as enum ('hashtag', 'keyword', 'followers', 'ubicacion');
exception when duplicate_object then null; end $$;

do $$ begin
  create type job_estado as enum ('pendiente', 'corriendo', 'ok', 'error');
exception when duplicate_object then null; end $$;

do $$ begin
  create type contacto_estado as enum ('nuevo', 'contactado', 'respondio', 'descartado');
exception when duplicate_object then null; end $$;

-- ── Función utilitaria: updated_at automático ────────────────────────────────
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- ── users ────────────────────────────────────────────────────────────────────
-- Auth propia (JWT del backend). password_hash con bcrypt.
create table if not exists users (
  id            uuid primary key default uuid_generate_v4(),
  email         text unique not null,
  password_hash text not null,
  nombre        text,
  rol           user_rol not null default 'operador',
  activo        boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists idx_users_rol on users(rol);
drop trigger if exists trg_users_updated on users;
create trigger trg_users_updated before update on users
  for each row execute function set_updated_at();

-- ── nichos ───────────────────────────────────────────────────────────────────
-- Definición reutilizable de un nicho: "médicos" con sus keywords, hashtags y
-- cuentas semilla (para buscar entre sus seguidores). usa_ia activa el
-- clasificador de Claude (Fase 4).
create table if not exists nichos (
  id              uuid primary key default uuid_generate_v4(),
  nombre          text not null,
  descripcion     text,
  keywords        text[] not null default '{}',   -- palabras esperadas en la bio
  hashtags        text[] not null default '{}',   -- sin el #
  cuentas_semilla text[] not null default '{}',   -- usernames semilla
  usa_ia          boolean not null default false,
  created_by      uuid references users(id) on delete set null,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists idx_nichos_nombre on nichos(nombre);
drop trigger if exists trg_nichos_updated on nichos;
create trigger trg_nichos_updated before update on nichos
  for each row execute function set_updated_at();

-- ── scrape_jobs ──────────────────────────────────────────────────────────────
-- Una búsqueda encolada. El backend la corre en background (Apify) y va
-- actualizando estado + total_encontrados.
create table if not exists scrape_jobs (
  id               uuid primary key default uuid_generate_v4(),
  nicho_id         uuid references nichos(id) on delete set null,
  angulo           job_angulo not null,
  query            text not null,               -- hashtag, keyword, o @cuenta
  filtros          jsonb not null default '{}',
  estado           job_estado not null default 'pendiente',
  total_encontrados integer not null default 0,
  total_nuevos     integer not null default 0,
  error_msg        text,
  created_by       uuid references users(id) on delete set null,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index if not exists idx_jobs_estado on scrape_jobs(estado);
create index if not exists idx_jobs_created on scrape_jobs(created_at desc);
drop trigger if exists trg_jobs_updated on scrape_jobs;
create trigger trg_jobs_updated before update on scrape_jobs
  for each row execute function set_updated_at();

-- ── ig_profiles ──────────────────────────────────────────────────────────────
-- Perfil público de IG. Dedup por username (idempotente): re-buscar actualiza
-- datos y scraped_at, no duplica.
create table if not exists ig_profiles (
  username        text primary key,
  full_name       text,
  bio             text,
  followers       integer,
  following       integer,
  posts           integer,
  is_business     boolean,
  category        text,
  external_url    text,
  email_publico   text,
  telefono_publico text,
  profile_pic_url text,
  ig_url          text,
  nicho_id        uuid references nichos(id) on delete set null,
  score_nicho     integer not null default 0,   -- 0..100 afinidad al nicho
  ia_veredicto    text,                          -- (Fase 4) 'si' | 'no' | 'dudoso'
  ia_motivo       text,
  scraped_at      timestamptz not null default now(),
  created_at      timestamptz not null default now()
);
create index if not exists idx_profiles_nicho on ig_profiles(nicho_id);
create index if not exists idx_profiles_score on ig_profiles(score_nicho desc);
create index if not exists idx_profiles_followers on ig_profiles(followers desc);

-- ── listas ───────────────────────────────────────────────────────────────────
create table if not exists listas (
  id          uuid primary key default uuid_generate_v4(),
  nombre      text not null,
  descripcion text,
  owner       uuid references users(id) on delete set null,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
drop trigger if exists trg_listas_updated on listas;
create trigger trg_listas_updated before update on listas
  for each row execute function set_updated_at();

-- ── lista_perfiles (N:M lista ↔ perfil, con estado de follow-up manual) ──────
create table if not exists lista_perfiles (
  id              uuid primary key default uuid_generate_v4(),
  lista_id        uuid not null references listas(id) on delete cascade,
  username        text not null references ig_profiles(username) on delete cascade,
  estado_contacto contacto_estado not null default 'nuevo',
  nota            text,
  created_at      timestamptz not null default now(),
  unique (lista_id, username)
);
create index if not exists idx_lp_lista on lista_perfiles(lista_id);
create index if not exists idx_lp_username on lista_perfiles(username);

-- ============================================================================
-- El backend accede con service_role (saltea RLS). Activar RLS en un archivo
-- aparte si en el futuro el frontend pega directo a Supabase.
-- ============================================================================
