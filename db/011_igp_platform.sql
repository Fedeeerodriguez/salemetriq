-- ============================================================================
-- IG PROSPECTOR dentro de la plataforma — Migración 011
--
-- Al integrarlo a SALEMETRIQ, la auth pasa a ser la de la plataforma
-- (public.users, superadmin). Por eso created_by / owner ahora guardan el id de
-- un usuario de la plataforma, NO de igp.users. Soltamos esos FK cross-tabla para
-- que no rompan (igp.users queda sin uso, se conserva por compatibilidad).
-- Idempotente.
-- ============================================================================

alter table igp.nichos       drop constraint if exists nichos_created_by_fkey;
alter table igp.scrape_jobs  drop constraint if exists scrape_jobs_created_by_fkey;
alter table igp.listas       drop constraint if exists listas_owner_fkey;
