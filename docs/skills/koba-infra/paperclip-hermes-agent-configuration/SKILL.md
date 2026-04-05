---
name: paperclip-hermes-agent-configuration
category: koba-infra
description: Configure Hermes agents in Paperclip — models, souls, adapters, and fixing common adapter failures.
---

# Paperclip Hermes Agent Configuration

## Context
Paperclip uses `adapter_type` and `adapter_config` to run agents. The `hermes_local` adapter spawns `hermes chat -q "prompt" -Q -m model` as a child process.

## Critical Findings

### 1. Model reads from `adapter_config.model`, NOT `runtime_config`
- Paperclip's hermes adapter reads the model from `adapter_config.model`
- `runtime_config` is ignored for model selection
- Default fallback is `anthropic/claude-sonnet-4` if no model is set

### 2. Update agent model in DB
```sql
UPDATE agents SET adapter_config = jsonb_build_object(
  'instructionsFilePath', '/root/koba/agents/{agent}.md',
  'model', 'qwen/qwen3.6-plus:free'
) WHERE name = 'AgentName';
```

### 3. `hermes` binary PATH issue
If Paperclip reports `Failed to start command "hermes"`, create a symlink:
```bash
ln -sf /root/.local/bin/hermes /usr/local/bin/hermes
systemctl restart kobaco.service
```

### 4. Adapter Config Fields (hermes_local)
| Field | Purpose |
|-------|---------|
| `instructionsFilePath` | Path to agent's soul.md file |
| `model` | Model string (e.g. `qwen/qwen3.6-plus:free`) |
| `timeoutSec` | Override default 300s timeout |
| `quiet` | Default true (uses `-Q` flag) |

### 5. Inject Tasks/Issues for Paperclip UI visibility
```sql
INSERT INTO issues (id, company_id, project_id, title, description, status, priority,
  assignee_agent_id, created_by_agent_id, request_depth, created_at, updated_at,
  completed_at, issue_number, identifier, origin_kind)
VALUES (gen_random_uuid(), '{company_id}', '{project_id}',
  'Task Title', 'Description here', 'completed', 'medium',
  '{agent_id}', '{agent_id}', 0, NOW(), NOW(), NOW(),
  {number}, 'KOB-{number}', 'manual');
```

### 6. Known Agent IDs (KobaCo)
| Agent | ID |
|-------|----|
| Koba | aef9e8b8-f8ee-42f1-b4b2-760136decec1 |
| CEO | f6326547-d39c-4b0a-8643-9b7bdf19b261 |
| Virdon | c0f59cc9-3370-40e8-96ed-8ebe203dbe34 |
| Lucio | 6d769de1-425b-4da1-9987-46b97cfd641e |
| Apolo | b0e6f439-4a67-41da-8103-70337f58a9f6 |
| Enzo | b9be1661-84f7-4be3-a10b-2b079b7763bc |
| Dalton | bdd49500-516f-4376-9110-3d3eacfeb5bd |
| Polar | 1bd98c6f-9190-421f-a41d-190ad5806f30 |
| Zantes | d5a591b6-afe6-47b0-826f-629d9924407b |
| Kira | 4afda399-3811-4e8b-8633-f26f27fd2cee |

## Remote DB Updates via Audio Bridge

The remote bridge (`https://audio-koba.cornelio.app/exec`) executes commands in **fresh shell sessions** — each call gets a new shell with no state persistence. You cannot write a file in one call and read it in another.

### Pattern: Execute SQL directly (no temp files)
Use `docker exec psql -c "SQL"` to run SQL without filesystem dependencies:

```python
import subprocess, json

adapter_config = json.dumps({
    "instructionsFilePath": "/root/koba/agents/agent.md",
    "model": "google/gemini-2.5-flash"
})
# Escape single quotes for SQL
escaped = adapter_config.replace("'", "''")

update_sql = f"UPDATE agents SET adapter_type='hermes_local', adapter_config='{escaped}', status='active', role='VP of Budgets', title='Agent - Title' WHERE id='UUID';"

# Pipe SQL directly to psql inside container (use -c, not -f)
result = subprocess.run(
    ["docker", "exec", "kobaco-db", "psql", "-U", "paperclip", "-d", "paperclip", "-c", update_sql],
    capture_output=True, text=True
)
```

### Pattern: Writing files on remote host
Use base64 encoding to avoid shell quoting hell:
```bash
echo {base64_content} | base64 -d > /path/to/file
```

### Pattern: Full remote script execution
Encode entire Python script as base64, pipe to python3:
```bash
echo {py_script_base64} | base64 -d | python3 2>&1
```
Then call via: `curl -s URL -X POST -H "Content-Type: application/json" -d '{"k":"limon8080","c":"CMD"}'`

## Pitfalls
- **Agent names are case-sensitive** — "CEO" not "Ceo", "Koba" not "KOBA"
- **Remote bridge sessions are NOT persistent** — each curl call gets a fresh shell. Write + execute in the same command chain.
- **psql -f fails on remote** — SQL files created on host aren't visible inside container. Use `docker exec psql -c "SQL"` instead.
- **Multiline SQL fails via bridge** — flatten to single line or use escaped single quotes (`'\\\\''`)
- **HERMES_AGENT_TIMEOUT** in `.env` doesn't affect Paperclip — Paperclip uses `timeoutSec` in adapter_config
- **No Telegram native support** — Paperclip doesn't have built-in Telegram. Use external daemon (`/root/koba/scripts/telegram_daemon.py`).
- **runtime_config is not read by hermes adapter** — all config goes in `adapter_config`