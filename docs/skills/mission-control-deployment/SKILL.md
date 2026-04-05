---
name: mission-control-deployment
category: devops
description: Deploy and configure Mission Control (builderz-labs) for AI agent orchestration using Docker and Cloudflare Tunnels.
---

# Mission Control Deployment

## Context
Mission Control serves as a dashboard for managing agent fleets, tasks, and spend.
**Repo:** https://github.com/builderz-labs/mission-control
**Instance:** `mc.cornelio.app` (Subdomain)

## 1. Docker Deployment
The image is pre-built and available on GHCR. It listens on port 3000 internally.

**Setup Command:**
```bash
docker run -d \
  --name mission-control \
  --restart unless-stopped \
  -p 4000:3000 \
  -v mc-data:/app/.data \
  ghcr.io/builderz-labs/mission-control:latest
```

**Notes:**
- Mapped to external port `4000` to avoid collisions (Host port 3000 is often used).
- Uses a named volume `mc-data` for persistence.

**Initial Setup:**
After starting, visit `http://<IP>:4000/setup` to create the Admin account.

## 2. Cloudflare Tunnel Configuration
If using an existing tunnel (e.g., the "koba" tunnel `2a1e9aa4...`):

1.  Go to **Cloudflare Zero Trust > Networks > Tunnels**.
2.  Select the active tunnel and go to the **Public Hostnames** tab.
3.  Click **Add a public hostname**.
4.  **Type:** `HTTPS` (or `HTTP` depending on origin config).
5.  **Subdomain:** `mc`
6.  **Domain:** `cornelio.app`
7.  **Service URL:** `http://localhost:4000` (The local port mapped in Docker).
8.  **Save**.

## 3. Connecting to Hermes Agent (Agent Setup Wizard)
To register an existing Hermes Agent (Koba) in Mission Control, use the **Set Up Hermes** wizard (accessible from the dashboard or `/setup`):

### Step 1: Hook
- Click **"Install Hook"**. This installs a reporter in `~/.hermes/hooks/mission-control/` on the machine where Hermes runs.
- The hook reports session events, activity, and status updates to MC.
- **Critical:** If setting up from a remote terminal (not on the VPS), the host must be reachable at the URL you configured. For the local VPS setup, ensure the agent is running on the same machine where the hook is installed.

### Step 2: Provider
- Configure the LLM provider (e.g., OpenRouter with `qwen/qwen3.6-plus:free`). This is the "fuel" for this agent registration.

### Step 3: Identity
- Customize the agent personality. Saved as `~/.hermes/SOUL.md`. Recommended for Koba:
  ```
  Name: Koba. Essence: AI Personal Assistant to Jose Navarro. Vibe: Tico (pura vida/tuanis), proactive, solution-oriented. Role: Problem solver. You speak directly, concisely, and focus on results.
  ```

### Step 4: Gateway
- This connects MC to the messaging channels (WhatsApp, Telegram, etc.).
- **Skip for now** if WhatsApp is already configured on the VPS via a separate hermes gateway (avoid conflicts). Configure later from MC dashboard.

### Step 5: Ready
- Agent appears in MC dashboard.

## 4. API Key Integration (Programmatic Access)
After setup, MC generates API keys for programmatic management (creating tasks, checking agents, etc.):
- Go to **Settings > API Keys** in MC dashboard.
- Generate a key. Store it securely in memory/config.
- Auth header format: `Authorization: Bearer mc_xxx` (verify exact format from dashboard, may vary).
- Base URL: `https://mc.cornelio.app/api`

## 5. Troubleshooting & Pitfalls

### Permission Denied / "Unauthorized" Loop
If the dashboard throws "Unauthorized" or the logs show `EACCES: permission denied, mkdir '/app/.next/cache'`:
1. The container was likely started as the default unprivileged user without proper volume ownership.
2. Fix: Stop container, remove it, and restart with `--user root`.
   ```bash
   docker rm -f mission-control
   docker run -d --name mission-control --restart unless-stopped --user root -p 4000:3000 -v mc-data:/app/.data ghcr.io/builderz-labs/mission-control:latest
   ```

### Setup Wizard "Stuck" at Login (No Sign Up option)
If you visit `/setup` and it redirects to Login without giving an option to create an Admin account, the internal database thinks an admin already exists (often from a failed previous attempt).
**Fix:**
1. Delete the data volume to force a fresh database creation: `docker volume rm mc-data`
2. Recreate the container with `--user root`.
3. Visit `/setup` **immediately** in an Incognito window.

### API Key Verification
- From **inside VPS**: `curl -s -H "Authorization: Bearer mc_xxx" http://localhost:4000/api/health`
- From **Agent Sandbox**: Cloudflare WAF often blocks the sandbox IP (403 Forbidden). Do not assume a 403 means the key is wrong; verify via VPS `curl` first.

### Authentication Issues
- The Setup Wizard may generate temporary keys that expire. If `Unauthorized` persists, go to Settings > API Keys and **Generate a New Key** manually.
- Keys usually start with the prefix `mc_`.

### Agent Setup Wizard
- **Hook Installation:** If setting up Hermes on the VPS where MC is hosted, the Hook must be installed via terminal on that VPS.
- **Gateway:** If the gateway is already running (e.g., WhatsApp), **Skip** this step in the wizard to avoid binding conflicts. Configure integration later via MC settings.
