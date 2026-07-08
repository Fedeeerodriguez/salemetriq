# Fase F — Closers por Fathom

Cuando un **closer** termina una llamada, Fathom la procesa y dispara un webhook
hacia SALEMETRIQ. El backend recibe el transcript, lo atribuye al closer correcto
dentro de su workspace y **dispara el análisis IA** (coaching) automáticamente.

Hay **dos formas** de conectar Fathom:

## Opción A (recomendada) — cada closer conecta su propia cuenta

Self-service, sin que el admin toque nada:

1. El closer entra a **Conexiones** en la app.
2. En la tarjeta **Fathom**, pega su **API key personal** (Fathom → Settings →
   Integrations → API) y toca **Conectar**.
3. El backend valida la key y **registra el webhook automáticamente** en la cuenta
   de Fathom del closer, apuntando a nuestro endpoint con un **token propio del
   usuario**. Desde ahí, sus llamadas entran solas y se atribuyen **directo a él**
   (no depende del email).

Requisito: el backend debe tener `PUBLIC_BACKEND_URL` configurada (la URL pública
del backend), porque Fathom necesita un destino HTTPS accesible para el webhook.
La API key se guarda **cifrada** (Fernet). Desconectar borra el webhook en Fathom.

## Opción B — un webhook por workspace (lo maneja el admin)

La atribución es **por token de workspace + email del closer**: cada workspace tiene
su propio `fathom_token` en la URL del webhook, y dentro de ese workspace la llamada
se asigna al closer cuyo email coincide con el host de Fathom.

## 1. Obtener la URL del webhook (como admin)

En la app → **Usuarios** → panel **"Conectar Fathom"** → copiá la URL. Se ve así:

```
https://TU-BACKEND/api/fathom/webhook?token=<fathom_token-del-workspace>
```

El token identifica tu workspace, así que **no lo compartas** entre clientes: cada
cliente tiene el suyo.

## 2. Configurar el webhook en Fathom

En Fathom → **Settings → Integrations → Webhooks** (o vía Zapier/Make apuntando al
mismo endpoint):

1. Creá un webhook nuevo con la URL del paso 1.
2. Activá **incluir transcript** en el payload (sin transcript no hay análisis).
3. (Opcional) incluí summary / action items — se guardan en `raw`.

El endpoint entiende el payload nativo "new meeting content ready" de Fathom
(`recorded_by.email`, `transcript` como array, `title`, `recording_start_time`,
`share_url`, `calendar_invitees`) y también formas aplanadas de Zapier/Make.

## 3. Atribución de closers

- Por defecto, la llamada se asigna al closer cuyo **email de login** coincide con
  el email del host en Fathom.
- Si un closer graba en Fathom con **otro email**, el admin lo setea en
  **Usuarios → (closer) → Fathom**. Ese override tiene prioridad.
- Si el host no matchea, se prueba con los invitados que sean closers del workspace.
- Si nadie matchea, la llamada **igual se guarda** en el workspace (sin closer) para
  que el admin la reasigne — no se pierde.

## 4. Qué pasa después

1. La grabación entra a `call_recordings` (idempotente por `provider + external_id`;
   si Fathom reenvía, se actualiza, no se duplica).
2. Si trae transcript, se dispara el **análisis IA** en segundo plano → aparece en
   **Call Analysis** con score, sentiment y coaching del closer.

## Seguridad

- Sin token válido → `HTTP 401`. El token es aleatorio por workspace.
- El backend usa la service_role key solo del lado servidor; el token del webhook
  no da acceso a nada más que a postear llamadas a ese workspace.
