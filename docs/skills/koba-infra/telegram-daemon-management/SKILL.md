---
name: telegram-daemon-management
category: koba-infra
description: Manage the Koba Telegram Multi-Bot Daemon (v4) — architecture, common fixes, group support, session persistence, and adding new bots.
---

# Telegram Daemon Management

The Koba Telegram Multi-Bot Daemon runs 10+ bot instances as separate threads, each polling Telegram's API and responding via `hermes chat -q`.

## Service Details
- **Script:** `/root/koba/scripts/telegram_daemon.py` (v4, upgraded from v3)
- **Service:** `koba-telegram.service` (systemd, running as root)
- **Logs:** `/var/log/koba_telegram.log` and `/var/log/koba_telegram_error.log`
- **State:** `/root/koba/telegram/offsets.json` (Telegram update offsets)
- **Sessions:** `/root/koba/telegram/sessions/` (session persistence JSON files)

## Common Issues and Fixes

### Bot Forgets Context (Apolo Problem)
**Symptom:** Agent loses memory after 1-2 minutes, doesn't remember previous messages.
**Root cause:** `hermes chat -q` is one-shot by default; no `--resume` flag used.
**Fix:** The v4 daemon now uses `session_key` to persist session IDs between calls.
- Session files stored in `/root/koba/telegram/sessions/{botname}_{key}.json`
- Uses `hermes -r {session_id}` for subsequent calls
- Also fix agent's Paperclip adapter_config: add `"persistSession": true` to jsonb

```sql
UPDATE agents SET adapter_config = adapter_config || '{"persistSession": true}'::jsonb
WHERE id = 'agent-uuid';
```

### Missing Koba Bot
v2-v3 didn't include Koba's own bot. V4 added it using the same Telegram token as Cornelio (shared bot identity).

### No Command Menu in Telegram
Bots show no `/menu` in Telegram. Fix: call `setMyCommands` API for each bot token.

```python
requests.post(f"https://api.telegram.org/bot{TOKEN}/setMyCommands",
    json={"commands": [{"command": "estado", "description": "Estado del agente"}]})
```

### Group Support
v3 only allowed private DMs from Jose. v4 added:
- `ALLOWED_USERS = {"7666543493", "50688218905"}` (Jose + Bachi)
- `ALLOWED_GROUPS = {"-1003752157454"}` (Los Inmortales)
- Mention detection (@BotName and entity-based)
- Conversation limit: max 6 messages per bot per group cycle (resets after 5 min)
- Bots ignore group messages unless: mentioned, or from Jose/Bachi

## Adding a New Bot
Add entry to the BOTS dict in the daemon script:
```python
"BotName": {"token": "BOT_TOKEN", "soul": "/root/koba/agents/botname.md", "model": "model/path"},
```

## Command Menu Structure
Each bot gets base commands (`/estado`, `/ayuda`) plus role-specific:
- **Apolo:** `/presupuesto`, `/planos`, `/materiales`
- **Koba:** `/equipo`, `/tareas`
- **Cornelio:** `/agentes`, `/tareas`
- **Virdon:** `/ventas`
- **Lucio:** `/marketing`
- **Dalton:** `/investigar`
- **Polar:** `/ads`

## Migration from v3 to v4
The v3→v4 migration script at `/tmp/migrate_v4.py` modifies the daemon in-place on the VPS, preserving bot tokens (which are redacted when viewed from outside).

**Steps:**
1. Backup current daemon: `cp telegram_daemon.py telegram_daemon.py.bak.$(date +%Y%m%d_%H%M%S)`
2. Run migration: `python3 /tmp/migrate_v4.py`
3. Verify syntax: `python3 -m py_compile /root/koba/scripts/telegram_daemon.py`
4. Restart: `systemctl restart koba-telegram.service`

## Pitfalls
- **Tokens redact** when read via SSH output from sandbox — always modify the file directly on the VPS
- **Python heredocs with quotes** fail in bash — write migration scripts to the VPS first, then run
- **Bots share rate limits** with Telegram API — add 25 second timeout, 1 second sleep between polls
- **Session keys** follow format `{botname}_dm_{userid}` or `{botname}_grp_{chatid}`
- **HERMES_AGENT_TIMEOUT=0** must be set in env to prevent session kills