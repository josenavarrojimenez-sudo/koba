---
name: kobaco-maintenance
category: koba-infra
description: Troubleshooting and maintenance for Kobaco (Paperclip) running on Hostinger VPS root. Covers systemd setup, database IP auto-detection, and common failures.
---

# Kobaco Maintenance Guide

## Context
Kobaco runs Paperclip directly on the Hostinger VPS (`srv1443323`), NOT inside the `kobaco-paperclip-1` container (which is a skeleton running `tail -f /dev/null`).
The app runs as a systemd service on the host using pnpm + tsx, connecting to Postgres inside `kobaco-db`.

## 1. Architecture
*   **Service:** `kobaco.service` (systemd, enabled, auto-restarts)
*   **Wrapper Script:** `/root/paperclip/run-kobaco.sh` - Auto-detects the current IP of `kobaco-db` via `docker inspect` and starts the server.
*   **Port:** `3200` -> `127.0.0.1`
*   **Cloudflare Tunnel:** Points to `localhost:3200` (managed via Cloudflare Zero Trust dashboard)

## 2. The Smart Startup Script (`/root/paperclip/run-kobaco.sh`)
This script is critical. It handles the dynamic IP issue where Docker reassigns `$IP` to `kobaco-db` on restart.

```bash
#!/bin/bash
cd /root/paperclip

# Auto-detect current DB IP
DB_IP=$(docker inspect kobaco-db --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
if [ -z "$DB_IP" ]; then
    echo "Error: No IP for kobaco-db"
    exit 1
fi

export PATH="/root/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export DATABASE_URL="postgresql://paperclip:paperclip123@${DB_IP}:5432/paperclip"
export PORT=3200
export HOST=127.0.0.1

/root/.hermes/node/bin/pnpm --filter @paperclipai/server dev
```

## 3. Current Systemd Service (`/etc/systemd/system/kobaco.service`)
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 4. Maintenance Operations

### Restart Kobaco
```bash
systemctl restart kobaco
sleep 10 && systemctl status kobaco --no-pager
```

### Check Logs (IP connection, port binding, errors)
```bash
journalctl -u kobaco -n 30 --no-pager
```

### Check Port 3200 Occupants
```bash
fuser 3200/tcp
```

### If Port 3200 is Busy (Stuck process)
```bash
systemctl stop kobaco
fuser -k 3200/tcp
systemctl start kobaco
```

## 5. Pitfalls
- **Dynamic DB IP:** `172.21.0.x` changes if `kobaco-db` is recreated. The script handles this, but if the service fails with `EHOSTUNREACH`, check if `kobaco-db` is actually running (`docker ps | grep kobaco-db`).
- **Zombie Skeleton:** `kobaco-paperclip-1` container (managed by Hostinger Docker Manager) might grab port 3200. If the service starts but you get 502, it might be silently binding to 3201. Kill the dummy container or its port mapping.
- **Node/Pnpm Path:** Systemd does not see the user's shell PATH. Never run raw commands in `ExecStart` — always use the bash wrapper script or set `Environment="PATH=..."`. Node is at `/root/.hermes/node/bin/node`.
- **Paperclip Dev Mode:** We are running `pnpm ... server dev` which uses `tsx`. This works but is technically "dev" mode. If performance becomes an issue, a `pnpm build` (creating `/server/dist`) and running `node server/dist/index.js` would be the production fix.
