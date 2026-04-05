---
name: paperclip-docker-deployment
description: Deploy Paperclip (paperclipai/paperclip) on managed Docker environments like Hostinger where `build:` is NOT supported. Paperclip has NO public Docker image — requires skeleton container + SSH-based build.
---

# Paperclip Docker Deployment (Managed Environments)

**Trigger:** Deploying Paperclip on Hostinger Docker Manager, Railway, or any managed Docker platform that cannot use `build:` context.

## Critical Discovery: NO Public Docker Image
- `paperclipai/paperclip:latest` → 404 (does NOT exist on Docker Hub)
- `paperclipai/server:latest` → 404 (does NOT exist on Docker Hub)
- GHCR (`ghcr.io/paperclipai/paperclip`) → requires authentication (401 Unauthorized)
- Official `docker/docker-compose.yml` uses `build: context: ..` which only works with local Docker, not managed platforms

**This is why the deployment always fails with "undefined volume" or hangs on image pull — the image doesn't exist.**

## Step-by-Step Deployment

### 1. Create Skeleton Container (Hostinger Compose UI)
Use a minimal YAML with the base Node.js image:

```yaml
services:
  kobaco:
    image: node:lts-trixie-slim
    container_name: kobaco-paperclip-1
    restart: always
    command: tail -f /dev/null
    ports:
      - "3200:3100"
    volumes:
      - kobaco_data:/paperclip

volumes:
  kobaco_data:
```

**Why this works:** The official Paperclip Dockerfile extends `node:lts-trixie-slim` anyway. The `tail -f /dev/null` keeps the container alive on Hostinger.

### 2. SSH into Host Server — Install & Build
You NEED SSH access to the host (managed Docker UI can't do this). Connect via paramiko, sshpass, or direct terminal.

```bash
# Install system deps + clone repo inside the container
docker exec kobaco-paperclip-1 bash -c "
  apt-get update && apt-get install -y git ripgrep curl &&
  corepack enable &&
  cd /paperclip &&
  git clone https://github.com/paperclipai/paperclip.git repo
"

# Install JS dependencies
docker exec kobaco-paperclip-1 bash -c "
  cd /paperclip/repo &&
  corepack enable && pnpm install
"
```

**Expected warnings:** `WARN Failed to create bin at ... ENOENT` — these are normal, caused by missing dist files that get created during build.

### 3. Build Paperclip (3 packages, in order)
```bash
docker exec kobaco-paperclip-1 bash -c "
  cd /paperclip/repo &&
  pnpm --filter @paperclipai/ui build &&
  pnpm --filter @paperclipai/plugin-sdk build &&
  pnpm --filter @paperclipai/server build &&
  test -f server/dist/index.js && echo 'BUILD SUCCESS'
"
```

Build takes ~20 seconds for UI, ~5 for plugin-sdk, ~10 for server.

### 4. Launch PostgreSQL Database
Paperclip REQUIRES PostgreSQL to start:

```bash
docker run -d --name kobaco-db --restart always \
  -e POSTGRES_USER=paperclip \
  -e POSTGRES_PASSWORD=<SECURE_PASSWORD> \
  -e POSTGRES_DB=paperclip \
  postgres:17-alpine
```

### 5. Connect DB to Same Docker Network
**CRITICAL:** The DB runs on `bridge` network by default, the paperclip container is on the Compose network. They can't see each other without connecting.

```bash
# Find the paperclip network name
docker inspect kobaco-paperclip-1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}'

# Connect DB to it (replace network name)
docker network connect <paperclip_network_name> kobaco-db
```

If you don't do this, the server crashes with: `getaddrinfo EAI_AGAIN kobaco-db`

### 6. Create Config File (REQUIRED before starting server)

Paperclip requires a valid JSON config matching its Zod schema. Without it, the server fails immediately.

Upload via SFTP to host, then copy to container:

```bash
docker exec kobaco-paperclip-1 mkdir -p /root/.paperclip/instances/default/data/{backups,storage}
docker exec kobaco-paperclip-1 mkdir -p /root/.paperclip/instances/default/{logs,secrets}
docker cp config.json kobaco-paperclip-1:/root/.paperclip/instances/default/config.json
```

**Config file structure (ALL fields are required):**

```json
{
  "$meta": {
    "version": 1,
    "updatedAt": "<ISO timestamp>",
    "source": "onboard"
  },
  "database": {
    "mode": "postgres",
    "connectionString": "postgres://user:pass@host:5432/database",
    "backup": {
      "enabled": true,
      "intervalMinutes": 60,
      "retentionDays": 30,
      "dir": "~/.paperclip/instances/default/data/backups"
    }
  },
  "logging": {
    "mode": "file",
    "logDir": "~/.paperclip/instances/default/logs"
  },
  "server": {
    "deploymentMode": "authenticated",
    "exposure": "public",
    "host": "0.0.0.0",
    "port": 3100,
    "allowedHostnames": ["your-domain.com"],
    "serveUi": true
  },
  "auth": {
    "baseUrlMode": "explicit",
    "publicBaseUrl": "https://your-domain.com"
  },
  "telemetry": {},
  "storage": {
    "provider": "local_disk",
    "localDisk": { "baseDir": "~/.paperclip/instances/default/data/storage" },
    "s3": { "bucket": "paperclip", "region": "us-east-1", "prefix": "", "forcePathStyle": false }
  },
  "secrets": {
    "provider": "local_encrypted",
    "strictMode": false,
    "localEncrypted": { "keyFilePath": "~/.paperclip/instances/default/secrets/master.key" }
  }
}
```

**CRITICAL: deploymentMode dictates host binding:**
- `local_trusted` → MUST use `host: "127.0.0.1"` (loopback only)
- `authenticated` → CAN use `host: "0.0.0.0"` (needed for public/Tunnel access)
- If you get error `local_trusted mode requires loopback host binding`, switch to `authenticated`.

### 7. Bootstrap CEO User

**MUST run in `authenticated` mode.** `local_trusted` mode rejects the command.

Use the direct Node CLI (pnpm may NOT be in PATH inside `docker exec`):

```bash
docker exec kobaco-paperclip-1 bash -c \
"cd /paperclip/repo && node cli/node_modules/tsx/dist/cli.mjs cli/src/index.ts auth bootstrap-ceo"
```

**NOT:** `pnpm paperclipai auth bootstrap-ceo` (pnpm won't be found in exec context).

This generates an invite URL like:
`https://your-domain.com/invite/pcp_bootstrap_<hash>`
Expiring in ~3 days.

### 8. Starting the Server
```bash
docker exec kobaco-paperclip-1 bash -c "
export DATABASE_URL='postgres://paperclip:<PASSWORD>@kobaco-db:5432/paperclip'
export BETTER_AUTH_SECRET='<random_base64>'
export PAPERCLIP_PUBLIC_URL='https://your-domain.com'
export PORT=3100
export HOST=0.0.0.0
export SERVE_UI=true
export PAPERCLIP_DEPLOYMENT_MODE=authenticated
export PAPERCLIP_DEPLOYMENT_EXPOSURE=private
export PAPERCLIP_HOME=/paperclip/instances/default
export NODE_ENV=production
export OPENCODE_ALLOW_ALL_MODELS=true

mkdir -p /paperclip/instances/default

cd /paperclip/repo
nohup node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js > /paperclip/server.log 2>&1 &
"
### 9. Starting the Server

**Must use:** `node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js` — Paperclip uses tsx for TypeScript even in production.

## Pitfalls: Bootstrap CEO Invite "Not Available"

The `bootstrap-ceo` invite can become invalid if:
1. The server process is killed and restarted (database state persists but invite timing/tokens may shift).
2. Multiple server instances run simultaneously on different ports (3101, 3102, etc.) — each writes different auth sessions.
3. The container is fully restarted (processes die, invite hash becomes stale).

**To fix:** Always ensure the server is running CLEAN (single instance, correct port), then regenerate the invite immediately with the direct CLI:
```bash
docker exec kobaco-paperclip-1 bash -c "cd /paperclip/repo && node cli/node_modules/tsx/dist/cli.mjs cli/src/index.ts auth bootstrap-ceo"
```

## Cloudflare Tunnel Setup

When using a Cloudflare Tunnel (Remote Managed) for the domain:

1. **DNS record** must be created in Cloudflare (A record pointing to CF IPs, or CNAME to the tunnel)
2. **Ingress rule** must be configured in the Cloudflare Zero Trust Dashboard:
   - Go to: Zero Trust → Networks → Tunnels → [Your Tunnel] → Public Hostnames
   - Add: `your-domain.com` → `http://localhost:3200`

**Error code 1033:** DNS exists, but no ingress rule routes to the origin. Configure the public hostname in the dashboard.

**Network mode matters:** If cloudflared runs in `host` network mode, `localhost:3200` works. If it's in bridge mode, use the paperclip container's internal IP with `http://172.xx.xx.xx:3100`.

## Pitfalls
1. **Wrong image names:** Never use `paperclipai/paperclip` or `paperclipai/server` — they don't exist. Always build from source.
2. **Server port is 3100** internally, not 3000 (see Dockerfile `EXPOSE 3100`).
3. **SERVE_UI=true** is mandatory or the UI won't be served — you get a raw API response.
4. **Network isolation:** `EAI_AGAIN` on DB hostname means containers are on different networks.
5. **setgroups errors** during apt-get in Hostinger containers — harmless, packages still install.
6. **Server binary:** Verify `server/dist/index.js` exists after build. If missing, the build failed.
7. **Server logs:** Check `/paperclip/server.log` inside the container for crash reasons.
8. **docker-entrypoint.sh NOT used:** When running manually (not via the official Dockerfile CMD), you invoke node directly with the tsx loader.
9. **`volumes:` block:** In Hostinger Compose UI, if you use named volumes, you MUST include the `volumes:` block at the root level of the YAML or it fails with `undefined volume`.
10. **Cloudflared host mode:** If cloudflared shares the host network namespace (`docker inspect --format '{{.HostConfig.NetworkMode}}'`), use `localhost:<mapped_port>` for ingress rules.

## Agent Management (Post-Deployment)

### CLI Limitations
Paperclip CLI has no `agent create` command. Available agent CLI commands:
- `paperclipai agent list --company-id <id>` — list agents (requires board access)
- `paperclipai agent get <agentId>` — get one agent (requires board access)
- `paperclipai agent local-cli <agentRef>` — create API key for existing agent

### API Structure
Routes are mounted at `/api` prefix. All write operations require board access or agent with canCreateAgents permission:
- `GET /api/health` — health check (public)
- All agent routes at `/agents/*` require company-level access
- Agent API keys (pcp_*) CANNOT create other agents — they get "Board access required"

### Agent Creation Schema (createAgentSchema)
```json
{
  "name": "AgentName",
  "role": "general",
  "title": "Role Title",
  "reportTo": "ceo-agent-id-uuid",
  "adapterType": "hermes_local",
  "adapterConfig": {},
  "runtimeConfig": {},
  "budgetMonthlyCents": 0,
  "permissions": {},
  "metadata": {}
}
```

### Available Adapter Types
`process`, `http`, `claude_local`, `codex_local`, `gemini_local`, `opencode_local`, `pi_local`, `cursor`, `openclaw_gateway`, `hermes_local`

### Creating Agents — Recommended Path
1. **Login via UI** at `https://your-domain.com` as the board user (from bootstrap CEO invite)
2. **Create a company** through the UI (required before creating agents)
3. **Create agents** via the company dashboard → "Create Agent" button
4. **Get API keys** from each agent's settings after creation
5. **Alternative**: Use `paperclipai agent local-cli <agentId>` from CLI to generate an API key for an existing agent

### CEO Permission Hierarchy
- CEO agents can create other agents automatically
- Agents with `permissions.canCreateAgents: true` can also create agents
- Non-CEO, non-creator agents CANNOT create other agents (get "Board access required")

### Creating Companies and Agents Directly via Database (Recommended for Automation)

Since the UI requires a board session and the API requires board cookies, the most reliable way to create companies and agents programmatically is direct SQL inserts into PostgreSQL. Current version: `0.3.1`.

**Step 1: Create the Company**
```sql
INSERT INTO companies (id, name, description, status, issue_prefix, issue_counter, require_board_approval_for_new_agents, feedback_data_sharing_enabled, created_at, updated_at)
VALUES (gen_random_uuid(), 'YourCompany', 'Description', 'active', 'ABC', 0, false, false, NOW(), NOW());
```

**Step 2: Create Board User Membership**
```sql
-- principal_type is 'user' or 'agent'; membership_role is 'owner', 'admin', or 'member'
INSERT INTO company_memberships (id, company_id, principal_type, principal_id, status, membership_role, created_at, updated_at)
VALUES (gen_random_uuid(), '<company-id>', 'user', '<user-id-from-user-table>', 'active', 'owner', NOW(), NOW());
```

**Step 3: Create Agents**
```sql
-- CEO agent
INSERT INTO agents (id, company_id, name, role, title, status, adapter_type, adapter_config, runtime_config, permissions, created_at, updated_at)
VALUES ('<uuid>', '<company-id>', 'Koba', 'ceo', 'CEO', 'active', 'hermes_local', '{}', '{}', '{"canCreateAgents": true}', NOW(), NOW());

-- Subordinate agent (reports to CEO)
INSERT INTO agents (id, company_id, name, role, title, status, reports_to, adapter_type, adapter_config, runtime_config, permissions, created_at, updated_at)
VALUES ('<uuid>', '<company-id>', 'Apolo', 'general', 'VP de Presupuestos', 'idle', '<ceo-agent-id>', 'openclaw_gateway', '{"gatewayUrl":"http://localhost:41607","adapterModel":"hermes-agent","timeoutSec":300,"maxTurnsPerRun":100}', '{}', '{}', NOW(), NOW());
```

**Step 4: Generate Agent API Key**
```sql
-- Paperclip stores SHA-256 hash of the key, not the raw key
-- Generate a key like: pcp_<name>_<40-char-hex>
-- Then hash it: SHA256(pcp_apolo_<hex>)
INSERT INTO agent_api_keys (id, agent_id, company_id, name, key_hash, last_used_at, revoked_at, created_at)
VALUES (gen_random_uuid(), '<agent-id>', '<company-id>', 'default', '<sha256-hex>', NULL, NULL, NOW());
```

**Available Agent Roles:** `ceo`, `cto`, `cmo`, `cfo`, `engineer`, `designer`, `pm`, `qa`, `devops`, `researcher`, `general`

**Available Adapter Types:** `process`, `http`, `claude_local`, `codex_local`, `gemini_local`, `opencode_local`, `pi_local`, `cursor`, `openclaw_gateway`, `hermes_local`

**Key DB Tables (v0.3.1):**
| Table | Key Columns | Notes |
|---|---|---|
| `companies` | id, name, issue_prefix, status | issue_prefix must be unique |
| `user` | id (text), name, email, email_verified | BetterAuth user table |
| `instance_user_roles` | id, user_id, role ('instance_admin' or 'board') | Board/instance admin mapping |
| `company_memberships` | company_id, principal_type, principal_id, membership_role | principal_type: 'user' or 'agent' |
| `agents` | id, company_id, name, role, title, reports_to (FK to agents.id), adapter_type, adapter_config (jsonb), runtime_config (jsonb), permissions (jsonb), status | reports_to enables org chart |
| `agent_api_keys` | id, agent_id, company_id, name, key_hash (SHA-256 hex) | key_hash = SHA256(raw_api_key) |
| `session` | id, user_id, expires_at | BetterAuth sessions |

**Pitfalls for Direct DB Creation:**
- The `user` table uses `text` type id (not uuid) for BetterAuth
- `company_memberships` uses `principal_type`/`principal_id` columns (NOT `user_id`/`member_type`)
- `agent_api_keys.key_hash` must be SHA-256 hex of the raw key string
- Company `issue_prefix` has a UNIQUE constraint
- Agent `reports_to` is a UUID FK to agents.id — must reference existing agent
- After DB inserts, the server auto-picks up changes (no restart needed) but heartbeat/scheduler may need a cycle
