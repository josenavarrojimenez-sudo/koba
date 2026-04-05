---
name: paperclip-agent-management
description: Manage Paperclip companies, agents, and API keys via direct DB access or API — for when CLI/board access is unavailable or you need bulk operations.
---

# Paperclip Agent Management

Guide for creating/managing Paperclip companies and agents via direct PostgreSQL access.

## Context
*   **Company ID:** `ebe7e870-9b29-4e42-beb0-37973d78e324` (Jose Navarro)
*   **Current Org Chart:**
    *   **Koba:** CEO & Personal Assistant (`aef9e8b8-f8ee-42f1-b4b2-760136decec1`)
    *   **Apolo:** VP of Budgets (Reports to Koba, `b0e6f439-4a67-41da-8103-70337f58a9f6`)
    *   **Virdon:** Sales Lead (Reports to Koba, `c0f59cc9-3370-40e8-96ed-8ebe203dbe34`) -> Enzo, Dalton
    *   **Lucio:** Marketing Lead (Reports to Koba, `6d769de1-425b-4da1-9987-46b97cfd641e`) -> Polar, Zantes, Kira

## Known Agent UUIDs (Koba Company)
| Agent | UUID | Model | Preset |
|---|---|---|---|
| Koba (CEO/Assistant) | aef9e8b8-f8ee-42f1-b4b2-760136decec1 | qwen/qwen3.6-plus:free | Seleccion de Jose |
| CEO | f6326547-d39c-4b0a-8643-9b7bdf19b261 | anthropic/claude-sonnet-4 | Los Cerebros |
| Virdon (Sales Lead) | c0f59cc9-3370-40e8-96ed-8ebe203dbe34 | minimax/minimax-m2.7 | Los Conversadores |
| Lucio (Marketing) | 6d769de1-425b-4da1-9987-46b97cfd641e | gpt-5.4-mini | Los Creativos |
| Apolo (Finance) | b0e6f439-4a67-41da-8103-70337f58a9f6 | anthropic/claude-sonnet-4 | Los Cerebros |
| Enzo (Closer) | b9be1661-84f7-4be3-a10b-2b079b7763bc | minimax/minimax-m2.7 | Los Conversadores |
| Dalton (Analyst) | bdd49500-516f-4376-9110-3d3eacfeb5bd | kimi/kimi-k2.5 | Los Bibliotecarios |
| Polar (Meta Ads) | 1bd98c6f-9190-421f-a41d-190ad5806f30 | minimax/minimax-m2.5:free | Paid Media |
| Zantes (Creative) | d5a591b6-afe6-47b0-826f-629d9924407b | gpt-5.4-mini | Los Creativos |
| Kira (Design) | 4afda399-3811-4e8b-8633-f26f27fd2cee | gpt-5.4-mini | UI/UX |

## Database Schema Reference
### Core Tables
- `agents` — `id`, `company_id`, `name`, `role`, `title`, `status`, `reports_to`, `adapter_type`, `adapter_config` (jsonb), `runtime_config` (jsonb), `permissions` (jsonb)
- `issues` — Task records visible in the UI (see `paperclip-task-injection` skill for schema)
- `activity_log` — Activity feed entries
- `company_memberships` — Links users/agents to (`principal_type`, `principal_id`)

### Adapter Types
- **`hermes_local`** (CURRENT standard) — Runs `hermes chat -q "prompt" -Q` locally. Requires `hermes` binary in PATH.
- **`openclaw_gateway`** (DEPRECATED) — Old WebSocket gateway adapter.
- Others: `claude_local`, `codex_local`, `cursor_local`, `gemini_local`, `opencode_local`, `process`, `http`

### adapter_config for hermes_local (CRITICAL)
The adapter reads from `adapter_config`, NOT `runtime_config`. Must include:
- `"instructionsFilePath"`: path to the agent's soul/instructions `.md` file
- `"model"`: the model to use (e.g., `"qwen/qwen3.6-plus:free"`)
- Optionally: `"hermesCommand"`, `"timeoutSec"`, `"provider"`, `"toolsets"`, `"quiet"`, `"persistSession"`

Example: `{"model": "qwen/qwen3.6-plus:free", "instructionsFilePath": "/root/koba/agents/koba.md"}`

## 🏆 REGLA DE ORO DE TRABAJO EN PAPERCLIP

### Flujo de Trabajo Estandarizado (aplica a TODOS los agentes)
1. **Koba detecta** archivo nuevo o tarea para un agente
2. **Koba crea** un workspace en `/root/koba/workspaces/{nombre}/` con archivos:
   - `00_WORKFLOW.md` — Pipeline completo y estado
   - `TASKS.md` — Checklist de fases con estado
   - `OUTPUT.md` — Donde Apolo pone el resultado final
   - `NOTES.md` — Log de actividad
   - `CONTEXTO.md` — Todos los datos extraidos del contexto
   - `data/` — Archivos procesados (JSON, Excel, imagenes)
3. **Koba crea issue en Paperclip** asignada al agente con descripcion completa
4. **Apolo (o agente X) ejecuta** la tarea siguiendo el pipeline
5. **Si hay problemas:** El agente crea issue adicional en Paperclip y notifica a Koba
6. **Koba revisa** issues y:
   - Si puede resolverlo: lo resuelve y cierra la issue
   - Si necesita ayuda de Jose: notifica a Jose con contexto y opciones
7. **Al terminar:** Agente llena `OUTPUT.md` con el resumen final y genera entregables en `data/`
8. **Koba notifica** a Jose con resumen y archivos entregables

### Jerarquia de Reportes
- **Jose Navarro** = Jefe de Jefes (ordenes directas, solo Koba le reporta)
- **Koba (CEO)** = Gestiona todos los agentes, resuelve issues, decide que escalar
- **Apolo (VP Presupuestos)** = Reporta a Koba, levanta issues si no puede resolver
- **Otros agentes** = Mismo patron: reportan a Koba, nunca directo a Jose

### Estado de Issues en Paperclip
- `todo` → Pendiente de comenzar
- `in_progress` → El agente esta trabajando
- `blocked` → El agente encontro problema, necesita ayuda de Koba
- `done` → Tarea completada, entregables listos
- `cancelled` → Tarea cancelada por Koba

### Notificaciones
- Koba notifica a Jose SOLO cuando:
  - Apolo esta bloqueado y Koba necesita una decision de Jose
  - La tarea fue completada exitosamente
  - Hay algo critico que requiere atencion humana
- Koba resuelve AUTOMATICAMENTE todo lo que pueda sin molestar a Jose

## Creating an Agent (SQL Pattern)
Use `docker exec` on the host because `psql` isn't installed there.
`docker exec kobaco-db psql -U paperclip -d paperclip -c "INSERT INTO agents (id, company_id, name, role, title, status, reports_to, adapter_type, permissions) VALUES (gen_random_uuid(), 'ebe7e870...', 'NAME', 'role', 'Title', 'idle', 'BOSS_UUID', 'openclaw_gateway', '{}');"`

## Creating an Agent API Key
Generate a raw key `pcp_<name>_hex`. Hash it SHA-256. Insert into `agent_api_keys`.
`INSERT INTO agent_api_keys (agent_id, company_id, name, key_hash, created_at) VALUES ('agent_uuid', 'company_id', 'default', encode(sha256('pcp_key'::bytea), 'hex'), NOW());`