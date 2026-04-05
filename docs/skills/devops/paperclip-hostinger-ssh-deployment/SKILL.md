---
name: paperclip-hostinger-ssh-deployment
category: devops
description: Deploy Paperclip on Hostinger via SSH (Manual Build) when the Compose GUI fails or requires custom images/volumes. Includes DB injection setup for custom agents and Audio Bridge integration.
---

# Paperclip Deployment on Hostinger (SSH Method)

Use this workflow when the UI Compose fails to pull images (e.g., private GHCR) or when you need absolute control over the build and database seeding.

## Pitfall: Skeleton Container vs Host Execution
The `node:lts-trixie-slim` skeleton container (`tail -f /dev/null`) is empty. **The Paperclip code lives on the HOST** at `/root/paperclip/`.

**Do NOT try to git clone inside the container.** Instead:
- Code lives at `/root/paperclip/` on the host
- Build/install deps on the host with node
- Run the server on the host
- The port-mapped container (`3200->3100`) is just an empty port-forwarder

**Debugging inside a minimal slim container:** No `ps`, `curl`, etc. Install them: `apt-get update && apt-get install -y procps curl` (or just debug from host level).

**pnpm PATH issue:** `npm install -g pnpm` often doesn't put it in PATH. Use `npx pnpm install` instead, or find it with `$(npm bin -g)/pnpm`.

## 1. Container Setup (Manual)
Instead of a private image, start a `node:slim` container as an empty port-forwarder. The code and server run on the host.

```dockerfile
docker run -d --name kobaco-paperclip-1 --restart always \
  --network <your_network> \
  -p 3200:3100 \
  -v kobaco_data:/paperclip \
  node:lts-trixie-slim \
  tail -f /dev/null
```

## 2. Build Phase
Enter the container to install, clone, and build.
```bash
docker exec kobaco-paperclip-1 bash -c "
  apt-get update -qq && apt-get install -y -qq git
  mkdir -p /paperclip/repo && cd /paperclip/repo
  git clone https://github.com/paperclipai/paperclip.git .
  corepack enable && pnpm install 2>&1 | tail -5
  pnpm --filter @paperclipai/ui build 2>&1 | tail -3
  pnpm --filter @paperclipai/plugin-sdk build 2>&1 | tail -3
  pnpm --filter @paperclipai/server build 2>&1 | tail -3
  test -f server/dist/index.js && echo BUILD_OK || echo BUILD_FAILED
"
```

## 3. Database Connection (HOST Level)
The DB container (`kobaco-db`) has port `5432` mapped internally to Docker network only. From the HOST, you must use the container's IP:

```bash
# Get the DB container IP
DB_IP=$(docker inspect kobaco-db --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
# Example result: 172.21.0.3

# Start server with correct DB URL
nohup bash -c 'export DATABASE_URL="postgresql://postgres:postgres@$DB_IP:5432/postgres?schema=public" && export PORT=3100 && export HOST=0.0.0.0 && npx pnpm --filter @paperclipai/server dev' > /root/paperclip/server.log 2>&1 &
```

Paperclip defaults to `local_trusted` which binds to `127.0.0.1`. For a public server behind a tunnel, you **must** use `authenticated` mode with `0.0.0.0`.

Create this file inside the container at `/root/.paperclip/instances/default/config.json`:
```json
{
  "$meta": { "version": 1, "updatedAt": "...", "source": "onboard" },
  "database": {
    "mode": "postgres",
    "connectionString": "postgres://paperclip:paperclip@kobaco-db:5432/paperclip"
  },
  "auth": { "baseUrlMode": "explicit", "publicBaseUrl": "https://kobaco.cornelio.app" },
  "server": {
    "deploymentMode": "authenticated",
    "exposure": "public",
    "host": "0.0.0.0",
    "port": 3100,
    "serveUi": true
  },
  "logging": { "mode": "file" }
}
```

## 4. Start the Server
Run the server with environment variables:
```bash
docker exec kobaco-paperclip-1 bash -c "
  export DATABASE_URL=postgres://...
  export BETTER_AUTH_SECRET=...
  export PORT=3100
  export HOST=0.0.0.0
  export PAPERCLIP_PUBLIC_URL=https://kobaco.cornelio.app
  cd /paperclip/repo
  nohup node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js > /paperclip/server.log 2>&1 &
"
```

## 5. Database Seeding (Bypassing Board Auth)
If the UI requires a Board Login that you don't have yet, inject directly into Postgres:
```sql
-- Create Company
INSERT INTO companies (id, name, ...) VALUES (..., 'Kobaco', ...);

-- Create "Board" membership
INSERT INTO company_memberships (..., principal_type, principal_id, ...) VALUES (..., 'user', '<user_id>', ...);
```

## 6. Audio Bridge (For Hermes Agent Access)
Since the agent sandbox cannot access the host's filesystem, create an API bridge:
1.  **Daemon**: `/opt/koba_audio_daemon.py` monitors OpenClaw's `inbound/*.ogg` folder.
2.  **Transcription**: Copies audio to host, calls ElevenLabs Scribe V2, saves text to `/home/node/.hermes/audio_inbound/LATEST_TRANSCRIPTION.json`.
3.  **HTTP Bridge**: `/opt/koba_audio_bridge.py` serves that JSON file on port 9999.
4.  **Cloudflare**: Route `audio-koba.cornelio.app` -> `http://localhost:9999` via the Tunnel.