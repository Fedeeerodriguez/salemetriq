-- ============================================================================
-- SALEMETRIQ — Migración 003: aislamiento de datos demo
--
-- Bandera `is_demo` en usuarios y en todas las tablas de datos. El backend
-- scopea cada lectura por el `is_demo` del usuario logueado:
--   - usuario demo  → ve solo filas is_demo = true
--   - usuario real  → ve solo filas is_demo = false
-- Así los datos demo quedan totalmente separados de los reales y solo se ven
-- con el usuario demo. Default false → toda ingesta/creación real es "no demo".
-- ============================================================================

alter table users             add column if not exists is_demo boolean not null default false;
alter table teams             add column if not exists is_demo boolean not null default false;
alter table leads             add column if not exists is_demo boolean not null default false;
alter table calls             add column if not exists is_demo boolean not null default false;
alter table setter_summaries  add column if not exists is_demo boolean not null default false;
alter table call_recordings   add column if not exists is_demo boolean not null default false;
alter table analysis_runs     add column if not exists is_demo boolean not null default false;
alter table metrics_daily     add column if not exists is_demo boolean not null default false;

create index if not exists idx_users_demo       on users(is_demo);
create index if not exists idx_calls_demo        on calls(is_demo);
create index if not exists idx_summaries_demo     on setter_summaries(is_demo);
create index if not exists idx_recordings_demo    on call_recordings(is_demo);
create index if not exists idx_analysis_demo      on analysis_runs(is_demo);
