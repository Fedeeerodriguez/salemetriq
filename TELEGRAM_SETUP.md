# Fase A — Setters por Telegram

Los **setters** mandan el resumen de cada setting a un bot de Telegram (texto o
nota de voz). El backend lo **estructura con Claude** (calificación del lead, si
agendó, próximo paso) y lo guarda en `setter_summaries`, atribuido al setter y a
su workspace (`team_id`) — respetando el aislamiento multi-tenant.

## 1. Crear el bot (2 minutos)

1. En Telegram, abrí **@BotFather** → `/newbot`.
2. Elegí un nombre (ej. `SALEMETRIQ`) y un username que termine en `bot`
   (ej. `SalemetriqBot`).
3. BotFather te da un **token** tipo `1234567890:AA...`. Copialo.

## 2. Configurar el backend

En `backend/.env`:

```
TELEGRAM_BOT_TOKEN=1234567890:AA...
TELEGRAM_WEBHOOK_SECRET=un-string-largo-y-secreto
```

(Opcional, frontend) para que el modal de "Vincular Telegram" muestre un link
directo al bot, en `frontend/.env`:

```
VITE_TELEGRAM_BOT=SalemetriqBot
```

## 3. Conectar el bot

### Producción (webhook)

Registrá la URL pública del backend (una sola vez):

```
cd backend
.venv/Scripts/python scripts/telegram_bot.py set-webhook https://TU-BACKEND/api/telegram/webhook
```

Telegram va a mandar cada mensaje a `POST /api/telegram/webhook`, validando el
secret. Listo.

### Local (polling, para probar sin URL pública)

```
cd backend
.venv/Scripts/python scripts/telegram_bot.py delete-webhook   # si registraste uno antes
.venv/Scripts/python scripts/telegram_bot.py poll
```

Deja el proceso escuchando y procesa los mensajes con el mismo código que el
webhook. Cortá con Ctrl+C.

## 4. Vincular a cada setter

1. En la app, como **admin**, entrá a **Usuarios**.
2. En la fila del setter, tocá **Telegram** → **Generar código** (ej. `SMQ-AB12CD`).
3. Pasale ese código al setter.
4. El setter abre el bot y envía: `/link SMQ-AB12CD`.
5. El bot confirma. A partir de ahí, cada mensaje que mande se carga como resumen.

Regenerar el código desvincula el chat anterior (útil si cambió de teléfono).

## 5. Notas de voz

Si configurás `OPENAI_API_KEY`, las notas de voz se transcriben con Whisper y se
procesan igual que el texto. Sin esa key, el bot le pide al setter que lo mande
por texto (no se pierde nada, solo no transcribe audio).

## Seguridad

- El webhook exige el header `X-Telegram-Bot-Api-Secret-Token` == `TELEGRAM_WEBHOOK_SECRET`.
- Un mensaje de un Telegram no vinculado recibe las instrucciones de `/link`; no
  se guarda nada hasta que exista el vínculo.
- El índice único sobre `telegram_user_id` impide que dos personas compartan el
  mismo chat.
