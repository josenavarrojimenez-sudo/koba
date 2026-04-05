---
name: paperclip-task-injection
category: koba-infra
description: Inject task records (issues) and activity_log entries into Paperclip's Postgres DB so they appear in the UI (kobaco.cornelio.app).
---

# Paperclip Task Injection

## Purpose
When Koba completes tasks via the remote bridge, inject them into Paperclip's `issues` and `activity_log` tables so Jose can see real-time progress in the `kobaco.cornelio.app` UI.

## Key IDs (fixed per company)
- **Company ID:** `ebe7e870-9b29-4e42-beb0-37973d78e324` (Koba)
- **Project ID:** `c193bfeb-593c-4c4b-ad1f-c353ea833f27` (Onboarding)
- **Koba Agent ID:** `aef9e8b8-f8ee-42f1-b4b2-760136decec1`

## DB Access
`psql` is NOT installed on Host. Use:
```bash
docker exec -i kobaco-db psql -U paperclip -d paperclip -c "SQL_HERE"
```

## Issues Table (visible in UI as tasks)
Key columns: `id (uuid)`, `company_id`, `project_id`, `title (text)`, `description (text)`, `status (text)`, `priority (text)`, `assignee_agent_id (uuid)`, `created_by_agent_id (uuid)`, `created_at`, `updated_at`, `completed_at (nullable)`, `started_at (nullable)`, `issue_number (int)`, `identifier (text like KOB-N)`, `origin_kind (text)`

**Status values:** `todo`, `in_progress`, `completed`, `cancelled`
**Priority values:** `low`, `medium`, `high`, `urgent`
**origin_kind:** Use `manual` for injected tasks

### Getting next issue_number
```sql
SELECT COALESCE(MAX(issue_number), 0) FROM issues;
```
Identifiers follow format `KOB-N`.

### Insert template
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
  gen_random_uuid(), '{company_id}', '{project_id}', NULL, NULL,
  'Task title', 'Description text', 'completed', 'high', '{agent_id}',
  'aef9e8b8-f8ee-42f1-b4b2-760136decec1', NULL, 0,
  NULL, NOW(), NOW(), NOW(), NULL,
  NOW(), {N}, 'KOB-{N}',
  NULL, NULL, NULL, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL, NULL,
  'manual', NULL, NULL
);
```

## Activity Log Table (visible in feed)
Key columns: `id (uuid)`, `company_id`, `actor_type (text)`, `actor_id (text)`, `action (text)`, `entity_type (text)`, `agent_id (uuid)`, `details (jsonb)`, `created_at`

```sql
INSERT INTO activity_log (id, company_id, actor_type, actor_id, action, entity_type, entity_id, agent_id, details, created_at)
VALUES (
  gen_random_uuid(), '{company_id}', 'agent', 'koba', 'task.completed',
  'agent', '{agent_id}', '{agent_id}',
  '{"details": "Task description here"}', NOW()
);
```

## Remote Bridge Access
The bridge is at `https://audio-koba.cornelio.app/exec`.
**Auth format (CRITICAL):** Must use `{"k": "limon8080", "c": "COMMAND"}` — NOT `secret`/`command`.
- `k` = the secret key
- `c` = the command to execute

## Pitfalls
- **Multiline SQL gives HTTP 500 through the bridge** — use single-line psql commands or escape properly
- **Single quotes in SQL** must be escaped as `'\''` when passing through the bridge
- **Agent names are case-sensitive in DB** — e.g., `CEO` not `Ceo`, `Koba` not `koba`
- **`assignee_agent_id`** must be a valid UUID from the `agents` table
- **`origin_kind='manual'`** marks these as user-injected (vs agent-executed)
- **HERMES_AGENT_TIMEOUT=0** in `.env` prevents 10-minute session kills from gateway
