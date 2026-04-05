---
name: paperclip-inter-agent-communication
category: koba-infra
description: Communicate with Paperclip agents (Apolo, Virdon, etc.) from Koba — reliable channels, what works from sandbox vs host, and workarounds when direct DB access is unavailable.
---

# Paperclip Inter-Agent Communication

Guide for Koba to communicate with and delegate to Paperclip agents (Apolo VP, Virdon Sales, etc.) from different execution environments.

## Environment Access Matrix

| Method | Hostinger Host | Sandbox (this agent) | Notes |
|--------|---------------|---------------------|-------|
| `hermes chat -q` | ✅ Works | ❌ Not installed | Best method from host |
| `docker exec kobaco-db psql` | ✅ May work | ❌ Not installed | Direct DB access |
| SSH to srv1443323 | ✅ (with key) | ❌ Permission denied | Need SSH key in sandbox |
| Paperclip API `/api/issues` | ✅ Unknown | ❌ 404 Not Found | No REST endpoint for issue creation |
| Paperclip API `/api/agents` | ✅ Unknown | ❌ Empty/timeout | Ports 3100/3200 unreachable |
| Bridge (localhost:9999/exec) | ✅ May work | ❌ Not running locally | Only runs from host |
| Browser (Playwright) | ❌ Chromium not installed | ❌ Chromium not installed | Both lack browser binaries |
| tmux hermes process | ✅ Works | ❌ Not installed | Spawna otro hermes en host |

## What Actually Works from Sandbox

**Direct communication with Paperclip agents is NOT possible from the sandbox.** Every method fails:
- No `hermes` CLI
- No `docker` command
- No `psql` 
- No SSH access (permission denied — publickey/password auth)
- No local Paperclip service
- Bridge not running in sandbox context
- No Playwright browser

## Workarounds (in order of preference)

### 1. Ask Jose to relay (quickest)
Provide the exact prompt Jose should paste into Paperclip's "Dar instrucciones" for the target agent:

```
[Instrucción para Apolo]
Koba (CEO) te indica: <instrucción específica>
Reporta el resultado directamente a Koba o generá los entregables en el workspace.
```

### 2. Jose provides Telegram context → Koba injects DB
If Jose shares what was discussed with an agent on Telegram:
- Koba creates the workspace structure on host
- Uses `hermes chat -q` on host (from another session/cron) to delegate
- Injects status into Paperclip via DB when access is available

### 3. Cron job on host
Use `cronjob` action to schedule a task that runs on the host where `hermes` CLI IS available:

```python
# This runs on the host environment
cronjob(action='create', prompt='Spawn Apolo workspace for K-18...', deliver='local')
```

## Agent UUIDs Reference
- **Koba (CEO):** aef9e8b8-f8ee-42f1-b4b2-760136decec1
- **Apolo (VP Budgets):** b0e6f439-4a67-41da-8103-70337f58a9f6
- **Virdon (Sales):** c0f59cc9-3370-40e8-96ed-8ebe203dbe34
- **Lucio (Marketing):** 6d769de1-425b-4da1-9987-46b97cfd641e
- **Company:** ebe7e870-9b29-4e42-beb0-37973d78e324
- **Project (Onboarding):** c193bfeb-593c-4c4b-ad1f-c353ea833f27

## Database Connection
```bash
# From Hostinger host (if docker is available):
docker exec -i kobaco-db psql -U paperclip -d paperclip -c "SQL_QUERY"

# Direct postgres connection (if psql installed):
PGPASSWORD=paperclip123 psql -h 172.21.0.3 -U paperclip -d paperclip -c "SQL_QUERY"
```

## Pitfalls
- **Never assume hermes CLI is in sandbox** — it's only on the host
- **SSH from sandbox to host fails** — need SSH keys configured
- **Paperclip has no REST API for issue creation** — must use DB or UI
- **Multiline SQL via bridge** → HTTP 500, must be single-line or properly escaped
- **Bridge auth format:** `{"k": "limon8080", "c": "COMMAND"}` NOT secret/command