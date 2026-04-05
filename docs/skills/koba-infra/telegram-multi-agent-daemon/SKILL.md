---
name: telegram-multi-agent-daemon
category: koba-infra
description: Deploy a multi-agent Telegram bot daemon that connects each bot to its Paperclip agent soul via Hermes CLI. Supports allowlists, per-agent models, and systemd management.
---

# Telegram Multi-Agent Daemon

## Architecture
A single Python daemon (`telegram_daemon.py`) runs multiple Telegram bots as threads. Each bot:
1. Long-polls Telegram Bot API for new messages
2. Filters by allowlist (user IDs)
3. Executes Hermes CLI with the agent's soul file + user message + assigned model
4. Sends the response back via Telegram

## Setup

### Daemon Location
- Script: `/root/koba/scripts/telegram_daemon.py`
- State: `/root/koba/telegram/offsets.json` (tracks last update_id per bot)
- Log: `/var/log/koba_telegram.log`

### Service
```bash
# File: /etc/systemd/system/koba-telegram.service
[Unit]
Description=Koba Telegram Multi-Bot Daemon
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /root/koba/scripts/telegram_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Key Configuration in the Script

```python
ALLOWLIST = {"7666543493"}  # Authorized Telegram user IDs

BOTS = {
    "AgentName": {
        "token": "BOT_TOKEN:HERE",
        "soul": "/root/koba/agents/agentname.md",
        "model": "provider/model-name",
    },
}
```

### How Message Processing Works

1. Bot receives text message from Telegram
2. Check `msg["from"]["id"]` against `ALLOWLIST` — reject if not allowed
3. Read agent's soul file (`adapter_config.instructionsFilePath`)
4. Build prompt: `Instructions:\n{soul}\n\n---\nUser says: {message}`
5. Execute: `hermes chat -q PROMPT -Q -m MODEL`
6. Parse output: strip everything after `session_id: <id>` line
7. Send response back via Telegram `sendMessage`

### Restart/Manage
```bash
systemctl restart koba-telegram.service
systemctl status koba-telegram.service  
journalctl -u koba-telegram.service -f
tail -f /var/log/koba_telegram.log
```

## Adding a New Bot
1. Add entry to `BOTS` dict with token, soul path, model
2. Update `ALLOWLIST` if needed
3. `systemctl restart koba-telegram.service`

## Pitfalls
- Telegram Bot API polling offset: always use `offset + 1` to avoid reprocessing
- Message text > 4000 chars must be truncated for Telegram API
- `getUpdates` timeout should be ~25-30s (long-polling)
- Each bot needs staggered start (`time.sleep(1)`) to avoid rate limits
- Voice notes, photos, etc. have no "text" field — handle separately if needed
- If Hermes CLI is not in PATH, use full path: `/root/.local/bin/hermes`
- The daemon requires `requests` library (usually pre-installed)
- For production, consider using webhooks instead of polling for better performance