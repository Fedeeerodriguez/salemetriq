-- 007_rls.sql — Activar Row Level Security en todas las tablas (deny-all)
--
-- El backend accede con la service_role key, que SALTEA RLS. El frontend NO
-- consulta Supabase directo (va todo por la API del backend). La anon key viaja
-- en el bundle del frontend, así que sin RLS cualquiera podría leer todo vía
-- /rest/v1. Activando RLS SIN políticas, los roles anon/authenticated quedan
-- denegados por completo, y el backend (service_role) sigue funcionando igual.
--
-- El keep-alive (anon key) devuelve HTTP 200 con lista vacía → sigue cumpliendo.

alter table users             enable row level security;
alter table teams             enable row level security;
alter table leads             enable row level security;
alter table calls             enable row level security;
alter table setter_summaries  enable row level security;
alter table call_recordings   enable row level security;
alter table analysis_runs     enable row level security;
alter table metrics_daily     enable row level security;
alter table transcript_chunks enable row level security;

-- Forzar RLS también para el dueño de las tablas (defensa en profundidad).
-- (No aplica a service_role, que tiene bypassrls.)
alter table users             force row level security;
alter table teams             force row level security;
alter table leads             force row level security;
alter table calls             force row level security;
alter table setter_summaries  force row level security;
alter table call_recordings   force row level security;
alter table analysis_runs     force row level security;
alter table metrics_daily     force row level security;
alter table transcript_chunks force row level security;
