-- 006_fathom.sql — Ingesta real de closers desde Fathom (webhook por workspace)
--
-- Cada workspace tiene su propio `fathom_token`: el admin configura en su cuenta
-- de Fathom un webhook apuntando a  /api/fathom/webhook?token=<fathom_token>.
-- El webhook resuelve el workspace por ese token y atribuye la grabación al closer
-- cuyo email coincide (fathom_email override, si no, el email de login).

alter table teams add column if not exists fathom_token text;

-- Backfill: un token aleatorio por cada team existente que no tenga.
update teams
   set fathom_token = substr(md5(random()::text || clock_timestamp()::text), 1, 24)
 where fathom_token is null;

create unique index if not exists idx_teams_fathom_token
  on teams(fathom_token) where fathom_token is not null;

-- Override opcional: si el email con el que el closer graba en Fathom difiere del
-- email de login, el admin puede setear este.
alter table users add column if not exists fathom_email text;
create index if not exists idx_users_fathom_email on users(fathom_email) where fathom_email is not null;
