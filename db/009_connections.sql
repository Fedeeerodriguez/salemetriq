-- 009_connections.sql — Conexión de Fathom por usuario (self-service)
--
-- Cada usuario conecta SU propia cuenta de Fathom pegando su API key. El backend
-- registra un webhook en Fathom apuntando a /api/fathom/webhook?token=<fathom_user_token>.
-- Como el token es del usuario, la llamada se atribuye directo a ese closer (sin
-- depender del match por email).

alter table users add column if not exists fathom_user_token    text;   -- token en la URL del webhook (identifica al usuario)
alter table users add column if not exists fathom_api_key_enc    text;   -- API key de Fathom, cifrada (Fernet)
alter table users add column if not exists fathom_webhook_id     text;   -- id del webhook creado en Fathom (para borrarlo al desconectar)
alter table users add column if not exists fathom_webhook_secret text;   -- secret HMAC que devuelve Fathom
alter table users add column if not exists fathom_connected_at   timestamptz;

create unique index if not exists idx_users_fathom_user_token on users(fathom_user_token) where fathom_user_token is not null;
