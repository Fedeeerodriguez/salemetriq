-- 008_onboarding.sql — Invitaciones (alta sin password) + branding de workspace
--
-- Flujo: se crea el usuario SIN password con un invite_token. El propio usuario
-- abre /invite/<token>, define su contraseña y queda activo. Así el admin/superadmin
-- no maneja contraseñas ajenas.

alter table users alter column password_hash drop not null;
alter table users add column if not exists invite_token   text;
alter table users add column if not exists invite_expires timestamptz;
create unique index if not exists idx_users_invite_token on users(invite_token) where invite_token is not null;

-- Branding del workspace (se muestra en el chip del topbar).
alter table teams add column if not exists brand_color text;   -- hex, ej '#7C3AED'
alter table teams add column if not exists logo_url    text;
