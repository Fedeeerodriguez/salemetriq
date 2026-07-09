-- ============================================================================
-- SALEMETRIQ — Migración 010: lead magnet (prueba gratuita)
--
-- Captura de leads del funnel de marketing: la landing pide email + teléfono y
-- entrega acceso a UNA prueba (analizar 1 llamada con IA). Tabla independiente
-- del multi-tenant (no pertenece a ningún workspace) — es el embudo comercial
-- de la plataforma + mentoría.
-- ============================================================================

create table if not exists trial_leads (
  id                uuid primary key default uuid_generate_v4(),
  email             text not null,
  telefono          text not null,
  token             text unique not null,          -- acceso a la prueba (localStorage del navegador)
  analisis_usados   integer not null default 0,
  max_analisis      integer not null default 1,    -- cupo gratis
  ultimo_analisis   jsonb,                          -- último resultado (para re-mostrarlo)
  origen            text,                            -- utm / fuente, opcional
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create unique index if not exists uq_trial_leads_email on trial_leads(lower(email));
create index if not exists idx_trial_leads_created on trial_leads(created_at desc);

drop trigger if exists trg_trial_leads_updated on trial_leads;
create trigger trg_trial_leads_updated before update on trial_leads
  for each row execute function set_updated_at();

-- RLS: el backend accede con service_role (saltea RLS). Sin políticas, la anon
-- key queda denegada (esta tabla nunca se toca desde el cliente).
alter table trial_leads enable row level security;
alter table trial_leads force row level security;
