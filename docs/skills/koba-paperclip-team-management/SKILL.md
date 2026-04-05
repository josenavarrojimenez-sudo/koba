---
name: koba-paperclip-team-management
category: koba-infra
description: Manage the Paperclip agent team (org chart, model presets, remote execution) for Kobaco.
---

# Koba Paperclip Team Management

## Team Structure

### Organigrama
```
🧠 Koba (CEO) ──→ hermes_local
├── 📊 Apolo (VP Presupuestos) ──→ hermes_local
├── 📈 Lucio (Líder Marketing) ──→ hermes_local
│   ├── 📱 Polar (Especialista Meta Ads) ──→ hermes_local
│   ├── 🎨 Zantes (Creativo Multimedia) ──→ hermes_local
│   └── ✏️ Kira (Diseñadora Visual) ──→ hermes_local
└── 💰 Virdon (Líder Ventas) ──→ hermes_local
    ├── 🤝 Enzo (Cerrador de Ventas) ──→ hermes_local
    └── 📝 Dalton (Analista Formalizador) ──→ hermes_local
```

### Company ID
`ebe7e870-9b29-4e42-beb0-37973d78e324`

### Key Agent IDs
- Koba: `aef9e8b8-f8ee-42f1-b4b2-760136decec1`
- Virdon: `c0f59cc9-3370-40e8-96ed-8ebe203dbe34`
- Lucio: `6d769de1-425b-4da1-9987-46b97cfd641e`
- Apolo: `b0e6f439-4a67-41da-8103-70337f58a9f6`

### Instructions Location
Each agent's `.md` file is at: `/root/koba/agents/{name_lower}.md`
Stored in `adapter_config.instructionsFilePath`.

### Remote Execution (Autonomy) — ⚠️ BROKEN
Daemon v8 exposes `POST /exec` at `https://audio-koba.cornelio.app/exec`

**Bridge health:** `/health` → `{"status": "alive", "version": "v8"}` ✅
**Exec endpoint:** `{"secret": "<SECRET>", "command": "bash_command"}`
**Exec auth:** ❌ FAILING — `{"err": "auth"}` with `limon8080` (secret rotated)

⚠️ **CURRENT BLOCKERS (as of Apr 5 2026):**
1. Bridge exec rejects ALL auth — `limon8080` no longer works
2. SSH to VPS (`root@srv1443323.hstgr.cloud`) → "Permission denied (publickey,password)"
3. Daemon source `/opt/koba_audio_daemon.py` does NOT exist on current host
4. Running from container (hostname `9dcee1ab8cf5`), NOT the VPS — no Docker, no psql, no access to VPS filesystem

**To fix agent autonomy:** Need valid SSH access to VPS to:
- Get current bridge secret from daemon source
- Verify bridge and daemon are actually running
- Deploy/fix systemd services for agents

### DB Access Pattern
`psql` is NOT on Host. Always use:
`docker exec kobaco-db psql -U paperclip -d paperclip -c "SQL_HERE"`

---

## Model Presets

Location: `/root/koba/docs/presets.json`
Switcher Script: `/root/koba/scripts/switch-preset.py`

### Available Presets
| Preset | Models (primary → fallbacks) |
|--------|-----|
| Los Cerebros | minimax-m2.7, qwen3.5-plus, mimo-v2-pro, gpt-5.4-mini, deepseek-v3.2 |
| Los Todoterreno | gemini-3-flash, gpt-5.4-mini, step-3.5-flash:free, gemini-2.5-flash |
| Los Programadores | mimo-v2-pro, qwen3.5-plus, step-3.5-flash:free, gemini-3-flash, gpt-5.4-mini |
| Los Creativos | gpt-5.4-mini, minimax-m2.7, gemini-3-flash, kimi-k2.5 |
| Los Bibliotecarios | kimi-k2.5, mimo-v2-pro, gemini-2.5-flash, qwen3.5-plus |
| Los Conversadores | minimax-m2.7, mimo-v2-pro, gemini-3-flash, grok-4.1-fast, gpt-5.4-mini |
| Los Obreros | gemini-2.5-flash, gemini-3-flash, gpt-5.4-mini, qwen3.5-plus |
| Los Compas | grok-4.1-fast, step-3.5-flash:free, gpt-5.4-mini, gemini-3-flash |
| Los Fotógrafos | gemini-3-flash, gpt-5.4-mini, gemini-2.5-flash, qwen3.5-plus |
| UI/UX | gpt-5.4-mini, gemini-3-flash, qwen3.5-plus, minimax-m2.5, deepseek-v3.2 |
| Caballitos de Batalla | step-3.5-flash, gemini-3-flash, qwen3.5-plus, gpt-5.4-mini |
| Seleccion de Jose | qwen/qwen3.6-plus:free, minimax-m2.7, step-3.5-flash, gpt-5.4-mini, gemini-2.5-flash |
| Paid Media | minimax-m2.5, step-3.5-flash:free, kimi-k2.5, gemini-2.5-flash, deepseek-v3.2 |
| Los Economicos | qwen/qwen3.6-plus:free, step-3.5-flash:free, nemotron-3-super-120b-a12b:free, minimax-m2.5:free, gemini-2.5-flash |

### Switching Presets
To switch all agents to a preset, use remote exec:
```bash
python3 /root/koba/scripts/switch-preset.py "Nombre del Preset" model1 model2 model3
```

Or via tunnel:
```json
POST https://audio-koba.cornelio.app/exec
{"k": "limon8080", "c": "python3 /root/koba/scripts/switch-preset.py 'Seleccion de Jose' 'qwen/qwen3.6-plus:free' 'minimax-m2.7' 'step-3.5-flash' 'gpt-5.4-mini' 'gemini-2.5-flash'"}
```

---

## Creating New Agents

1. **Create instruction file**: `/root/koba/agents/{name_lower}.md`
2. **Insert into DB** (via docker exec):
```sql
INSERT INTO agents (id, company_id, name, role, title, status, reports_to, adapter_type, adapter_config, permissions, runtime_config, created_at, updated_at)
VALUES (gen_random_uuid(), 'ebe7e870-9b29-4e42-beb0-37973d78e324', 'Nombre', 'general', 'Titulo', 'idle', '<boss_agent_id>', 'hermes_local', '{"instructionsFilePath": "/root/koba/agents/nombre.md"}'::jsonb, '{}'::jsonb, jsonb_build_object('fallbackModels', ARRAY['qwen/qwen3.6-plus:free','minimax-m2.7','step-3.5-flash','gpt-5.4-mini','gemini-2.5-flash'], 'preset', 'Seleccion de Jose'), now(), now());
```

### Pitfalls
1. **Adapter type**: Always use `hermes_local`, NEVER `openclaw_gateway`
2. **DB access**: `psql` is only inside `kobaco-db` container, never on host
3. **Sandbox isolation**: Commands from Koba's AI sandbox cannot reach VPS filesystem directly — use the `/exec` tunnel endpoint
4. **Heredoc escaping**: When writing scripts via SSH/tunnel, always use `cat << 'EOF'` (single-quoted EOF prevents shell expansion)
5. **JSON escaping**: When building SQL with JSONB from strings, avoid shell escaping nightmares — use Python scripts written via heredoc instead of inline SQL
6. **HERMES_AGENT_TIMEOUT**: The gateway kills agent sessions at 10 minutes by default. This is a gateway/environment variable, NOT a model fallback issue. Fix: add `HERMES_AGENT_TIMEOUT=0` to `/root/.hermes/.env`. From agent side, avoid this by keeping individual tool calls under 2 minutes, using subagents for parallel work, and setting explicit timeouts.
7. **Docker /tmp mapping**: Docker does NOT auto-map host `/tmp` into containers. Piping SQL through `docker exec ... psql` (stdin pipe) works better than passing file paths.
8. **Bridge secret format**: The daemon uses `{"secret": "...", "command": "..."}` body format, NOT `{"k": "...", "c": "..."}`. Verify the actual key names by inspecting the daemon source.