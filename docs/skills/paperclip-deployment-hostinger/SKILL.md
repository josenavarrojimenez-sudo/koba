---
name: paperclip-deployment-hostinger
description: Deploy Paperclip on Hostinger VPS via Docker Manager by using a minimal base image, then setting up a persistent systemd service on the Host to run the actual server (more stable than 'docker exec').
---

# paperclip-deployment-hostinger

Paperclip does not provide a public Docker image on Docker Hub that works seamlessly with Hostinger's Compose manager. To bypass this, we deploy a minimal Node container (skeleton) for the UI/Port, but run the **real server via systemd on the Host** (to avoid losing the process on container restart and to handle dynamic DB IPs).

## 1. Docker Compose Skeleton
Deploy this `yaml` in Hostinger Docker Manager. This keeps port 3200 open for Cloudflare and provides the DB:

```yaml
services:
  paperclip-app:
    image: node:lts-trixie-slim
    container_name: paperclip-app
    restart: always
    command: tail -f /dev/null
    ports:
      - "3200:3100"
    volumes:
      - paperclip_data:/paperclip
  paperclip-db:
    image: postgres:17-alpine
    container_name: paperclip-db
    restart: always
    environment:
      POSTGRES_USER: paperclip
      POSTGRES_PASSWORD: paperclip123
      POSTGRES_DB: paperclip
    volumes:
      - paperclip_db:/var/lib/postgresql/data

volumes:
  paperclip_data:
  paperclip_db:
```

## 2. SSH & Install Dependencies
SSH into the Hostinger VPS:

```bash
# Install dependencies
cd /root && git clone https://github.com/paperclipai/paperclip.git paperclip
cd /root/paperclip
npm install -g tsx
npm install -g pnpm
# Or use npx if global install fails
# npm install -g corepack && corepack enable pnpm

pnpm install
```

## 3. Systemd Service (The Production Way)
Do not use `docker exec nohup`. Use systemd with a wrapper script that handles dynamic DB IPs.

**Create the wrapper script:** `/root/paperclip/run-kobaco.sh`
```bash
#!/bin/bash
cd /root/paperclip

# Detect IP of the DB container (changes on restart!)
DB_IP=$(docker inspect kobaco-db --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

if [ -z "$DB_IP" ]; then
    echo "Error: No se encontro IP para kobaco-db"
    exit 1
fi

echo "Arrancando Kobaco conectando a Postgres en $DB_IP"

export PATH="/root/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export DATABASE_URL="postgresql://paperclip:paperclip123@${DB_IP}:5432/paperclip"
export PORT=3200
export HOST=127.0.0.1

/root/.hermes/node/bin/pnpm --filter @paperclipai/server dev
```
`chmod +x /root/paperclip/run-kobaco.sh`

**Create the service:** `/etc/systemd/system/kobaco.service`
```ini
[Unit]
Description=Kobaco Paperclip Server
After=docker.service
Wants=docker.service

[Service]
Type=simple
WorkingDirectory=/root/paperclip
ExecStart=/bin/bash /root/paperclip/run-kobaco.sh
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
systemctl daemon-reload && systemctl enable kobaco && systemctl start kobaco
```

## Pitfalls

### Critical Lessons Learned
1. **Container Zombie**: The skeleton container (`tail -f /dev/null`) keeps showing "Running" even if the App inside crashes. Always check logs, not just UI status.
2. **Bad Gateway 502**: If the server crashes or moves ports (e.g. from 3200 to 3201 because of a port conflict), Cloudflare will show 502. Kill the zombie container (`docker stop paperclip-app`) before running the server on the Host directly on port 3200.
3. **Deployment mode**: `local_trusted` REQUIRES `host: "127.0.0.1"` and fails with `0.0.0.0`.
4. **Postgres Auth Failure**: The container DB uses `paperclip`/`paperclip123`. If you get `ECONNREFUSED` or `auth_failed`, verify the password in `docker inspect paperclip-db`.
5. **Path Issues in Sandboxes**: `pnpm` is often not in the PATH in systemd environment. Use a bash wrapper script (like `run-kobaco.sh`) and export the full PATH (`/root/.hermes/node/bin:...`).
6. **Dynamic DB IPs**: Docker changes the container IP on restart. The wrapper script (`run-kobaco.sh`) solves this by using `docker inspect` to find the current IP before starting the server.