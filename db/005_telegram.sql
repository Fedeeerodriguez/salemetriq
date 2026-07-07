-- 005_telegram.sql — Vinculación de setters con Telegram (Fase A)
--
-- Cada setter se vincula a la plataforma enviando `/link CODIGO` al bot de
-- Telegram. El admin genera el código desde la página Usuarios y se lo pasa al
-- setter. Una vez vinculado, guardamos su telegram_user_id y todo mensaje que
-- envíe se atribuye a su setter_id + team_id (multi-tenant).

alter table users add column if not exists telegram_user_id  bigint;
alter table users add column if not exists telegram_link_code text;

-- Un chat de Telegram = un solo usuario; un código = un solo usuario.
create unique index if not exists idx_users_telegram_uid  on users(telegram_user_id) where telegram_user_id is not null;
create unique index if not exists idx_users_telegram_code on users(telegram_link_code) where telegram_link_code is not null;

-- Origen del resumen (whatsapp | telegram | manual | web). Útil para saber por
-- dónde entró cada setter_summary.
alter table setter_summaries add column if not exists fuente text default 'manual';
