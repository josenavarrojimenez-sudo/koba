---
name: koba-telegram-multibot-daemon
category: koba-infra
description: Deploy and manage the multi-bot Telegram daemon that connects all KobaCo agents to Telegram with direct Hermes execution.
---

# Koba Telegram Multi-Bot Daemon

## Overview
A Python daemon (`/root/koba/scripts/telegram_daemon.py`) that polls Telegram for 9+ bot tokens simultaneously, executes Hermes CLI with each agent's soul file, and delivers responses back.

## Architecture
- **Single process**, multi-threaded (one thread per bot)
- **Allowlist-based** — only authorized Telegram user IDs get responses (Jose's ID: 7666543493)
- **Direct Hermes execution** — runs `hermes chat -q "soul + message" -Q -m model` per message
- **Offset tracking** — persists in `/root/koba/telegram/offsets.json`
- **No Telegram libraries needed** — uses raw Telegram Bot API via HTTP requests

## Configuration
Each bot has:
```python
"AgentName": {"token": "BOT_TOKEN", "soul": "/root/koba/agents/agent.md", "model": "model/string"}
```

## Management Commands
```bash
# Status
systemctl status koba-telegram.service
tail -f /var/log/koba_telegram.log

# Restart
systemctl restart koba-telegram.service

# Check offsets (which messages have been processed)
cat /root/koba/telegram/offsets.json
```

## Adding a new bot
1. Create the bot via BotFather on Telegram, get the token
2. Add entry to the `BOTS` dict in `/root/koba/scripts/telegram_daemon.py`
3. Add the user ID to the `ALLOWLIST` set
4. Ensure the agent has a soul file at the specified path
5. Restart: `systemctl restart koba-telegram.service`

## Pitfalls
- **Allowlist is a Python set of strings** — user IDs must be strings, not integers
- **No voice note support** — currently only processes text messages
- **Hermes timeout** — default 120s per message. Long-running tasks may timeout.
- **Polling interval** — 1 second between polls per bot. 9 bots = ~9 requests/second minimum.
- **Offset loss** — if offsets.json is deleted, the bot re-processes old messages. Keep the file safe.
- **No rate limiting on Telegram send** — if Hermes response > 4000 chars, it gets truncated.
- **systemd log rotation** — logs go to `/var/log/koba_telegram.log` (append mode in systemd).