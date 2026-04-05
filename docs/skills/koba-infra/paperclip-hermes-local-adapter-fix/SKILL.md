---
name: paperclip-hermes-local-adapter-fix
category: koba-infra
description: Troubleshooting and fixing the hermes_local adapter in Paperclip — resolves "Failed to start command hermes" and model mismatch errors.
---

# Paperclip Hermes Local Adapter Fix

## Symptoms
- **"Failed to start command 'hermes' in '.'"** — Paperclip can't find the `hermes` binary in its PATH
- **Wrong model used** — Paperclip uses default `anthropic/claude-sonnet-4` instead of the configured model
- **"adapter_failed"** in the Run UI

## Diagnosis

### 1. Check if hermes is accessible
```bash
which hermes  # Should return /root/.local/bin/hermes
hermes version  # Should show Hermes Agent version info
```

### 2. Check if it's in Paperclip's PATH
```bash
cat /proc/$(pgrep -f 'tsx.*src/index' | head -1)/environ | tr '\0' '\n' | grep PATH
```
Look for `/usr/local/bin` in the PATH.

### 3. Check adapter config
```bash
docker exec -i kobaco-db psql -U paperclip -d paperclip -c "SELECT name, adapter_type, adapter_config FROM agents ORDER BY name;"
```

## Fixes

### Fix 1: Binary not found (PATH issue)
Create a symlink in a directory that IS in Paperclip's PATH:
```bash
ln -sf /root/.local/bin/hermes /usr/local/bin/hermes
# Then restart Paperclip to pick up the new PATH:
systemctl restart kobaco.service
```

### Fix 2: Wrong model (adapter_config vs runtime_config)
The `hermes_local` adapter reads from **`adapter_config`**, NOT `runtime_config`.

The adapter (in `hermes-paperclip-adapter`) looks for these keys in `adapter_config`:
- `model` — the model to pass to `hermes chat -m`
- `instructionsFilePath` — path to the agent's soul/instructions file
- `timeoutSec` — execution timeout (default 300)
- `provider` — provider name (valid: auto, openrouter, nous, zai, kimi-coding, minimax, minimax-cn)
- `toolsets` — comma-separated toolset names
- `quiet` — use -Q flag (default true)
- `hermesCommand` — override binary path/name

CRITICAL: Do NOT put `model` in `runtime_config` — Paperclip ignores it there.

Update command:
```sql
UPDATE agents SET adapter_config = jsonb_build_object(
  'instructionsFilePath', '/root/koba/agents/NAME.md',
  'model', 'qwen/qwen3.6-plus:free'
) WHERE name = 'AgentName';
```

### Fix 3: Service needs restart
After any filesystem change (new symlink, new binary), Paperclip must restart:
```bash
systemctl restart kobaco.service
```

## How the Adapter Works
The `hermes_local` adapter spawns: `hermes chat -q "PROMPT" -Q -m MODEL`
- `-q` / `--query`: single query mode (non-interactive)
- `-Q` / `--quiet`: no banner/spinner, only response + session_id
- `-m` / `--model`: model name (e.g., `qwen/qwen3.6-plus:free`)
- `-t` / `--toolsets`: comma-separated toolsets
- `--provider`: inference provider (optional, auto-detected from model name)

The prompt includes a Paperclip identity block and task assignment instructions.
The adapter parses session_id from output line: `session_id: <id>`

## Pitfalls
- Agent names are case-sensitive: `CEO` not `Ceo`
- The bridge uses `{"k": "secret", "c": "command"}` format, not `secret`/`command`
- Multiline SQL through the bridge gives HTTP 500 — use single-line commands
- Default model in adapter constants is `anthropic/claude-sonnet-4` — will use this if not overridden

## Task Injection (Visibility in Paperclip UI)
To make tasks visible in the Paperclip UI, inject them as **issues** in the DB:

```sql
INSERT INTO issues (
  id, company_id, project_id, goal_id, parent_id,
  title, description, status, priority, assignee_agent_id,
  created_by_agent_id, created_by_user_id, request_depth,
  billing_code, created_at, updated_at, completed_at, cancelled_at,
  started_at, issue_number, identifier,
  hidden_at, checkout_run_id, execution_run_id,
  execution_agent_name_key, execution_locked_at, assignee_user_id,
  assignee_adapter_overrides, execution_workspace_settings,
  project_workspace_id, execution_workspace_id, execution_workspace_preference,
  origin_kind, origin_id, origin_run_id
) VALUES (
  gen_random_uuid(),
  'COMPANY_ID', 'PROJECT_ID', NULL, NULL,
  'Task Title', 'Task Description',
  'completed', 'high',
  'AGENT_UUID', 'AGENT_UUID', NULL, 0,
  NULL, NOW(), NOW(), NOW(), NULL,
  NULL, ISSUE_NUMBER, 'KOB-NUMBER',
  NULL, NULL, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL,
  'manual', NULL, NULL
);
```

Key fields:
- `status`: `todo`, `in_progress`, `completed`, `cancelled`
- `origin_kind`: `manual` for injected tasks
- `identifier`: `KOB-{N}` format (matches issue_number)
- `assignee_agent_id`: which agent owns the task

Activity log entries can be added to the `activity_log` table for feed visibility.