-- ============================================================================
-- SALEMETRIQ — Migración 004: multi-tenant (workspaces)
--
-- Cada cliente = un workspace (teams). Los usuarios pertenecen a un workspace y
-- solo ven datos de su workspace. La plataforma (nosotros) tiene superadmins que
-- dan de alta clientes.
--
--   users.is_superadmin  → plataforma (nosotros), fuera de todo workspace
--   teams.owner_id       → usuario admin dueño del workspace (el cliente)
--   teams.plan           → plan comercial
--   <tabla>.team_id      → workspace al que pertenece cada fila de datos
--
-- El aislamiento pasa de is_demo (demo/real) a team_id (por workspace). is_demo
-- se conserva solo como marca del workspace demo.
-- ============================================================================

-- Plataforma / superadmin
alter table users add column if not exists is_superadmin boolean not null default false;

-- Workspace: dueño y plan
alter table teams add column if not exists owner_id uuid references users(id) on delete set null;
alter table teams add column if not exists plan text default 'standard';

-- team_id en las tablas de datos que aún no lo tienen (leads ya lo tiene)
alter table calls             add column if not exists team_id uuid references teams(id) on delete cascade;
alter table setter_summaries  add column if not exists team_id uuid references teams(id) on delete cascade;
alter table call_recordings   add column if not exists team_id uuid references teams(id) on delete cascade;
alter table analysis_runs     add column if not exists team_id uuid references teams(id) on delete cascade;
alter table metrics_daily     add column if not exists team_id uuid references teams(id) on delete cascade;

create index if not exists idx_calls_team      on calls(team_id);
create index if not exists idx_summaries_team  on setter_summaries(team_id);
create index if not exists idx_recordings_team on call_recordings(team_id);
create index if not exists idx_analysis_team   on analysis_runs(team_id);
create index if not exists idx_metrics_team    on metrics_daily(team_id);
create index if not exists idx_teams_owner     on teams(owner_id);

-- ── Backfill: el workspace demo se queda con todos los datos demo ────────────
update calls c
  set team_id = t.id from teams t
  where t.is_demo and c.is_demo and c.team_id is null;
update setter_summaries s
  set team_id = t.id from teams t
  where t.is_demo and s.is_demo and s.team_id is null;
update call_recordings r
  set team_id = t.id from teams t
  where t.is_demo and r.is_demo and r.team_id is null;
update analysis_runs a
  set team_id = t.id from teams t
  where t.is_demo and a.is_demo and a.team_id is null;

-- Dueño del workspace demo = usuario demo; superadmin de plataforma = admin
update teams set owner_id = u.id
  from users u where teams.is_demo and u.email = 'demo@salemetriq.com';
update users set is_superadmin = true where email = 'admin@salemetriq.com';
