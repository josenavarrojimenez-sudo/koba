---
name: kobaco-systemd-hardening
category: koba-infra
description: Fix Kobaco 502 errors and DB connectivity by running Paperclip on Host via Systemd (Dynamic IP Resolution). Use when the Paperclip container is a skeleton or DB IP changes.
---

# Kobaco Systemd Hardening & Host Resilience

## Context
The Hostinger `kobaco-paperclip-1` container is often a "skeleton" (running `tail -f /dev/null`) and fails to serve the app, causing **502 Bad Gateway**.
Additionally, the Postgres container (`kobaco-db`) **changes IP** on restart, breaking hardcoded connection strings.
Systemd often fails to launch Node apps due to `PATH` issues (e.g. `status=127` or `203/EXEC`).

**Solution:** Run the Paperclip server source code directly on the VPS Host (in `/root/paperclip`) wrapped in a systemd service that dynamically resolves the DB IP.

## Procedure

### 1. Clean Up
Ensure the zombie container is removed so it doesn't hog port `3200`:
```bash
docker stop kobaco-paperclip-1
docker rm kobaco-paperclip-1
```

### 2. Install Dependencies (Host)
Ensure `pnpm` is available and deps are installed:
```bash
cd /root/paperclip
npm install -g pnpm
npx pnpm install
```

### 3. Create Dynamic IP Script
This script finds the DB IP automatically. Create `/root/paperclip/run-kobaco.sh`:

```bash
#!/bin/bash
cd /root/paperclip

# 1. Find current DB IP dynamically
DB_IP=$(docker inspect kobaco-db --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

if [ -z "$DB_IP" ]; then
    echo "Error: DB IP not found. Is 'kobaco-db' running?"
    exit 1
fi

echo "Starting Kobaco. Connecting to Postgres at $DB_IP..."

# Fix PATH for Hostinger Node/Pnpm locations
export PATH="/root/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin"

export DATABASE_URL="postgresql://paperclip:paperclip123@${DB_IP}:5432/paperclip"
export PORT=3200
export HOST=127.0.0.1

# Run app via local pnpm
node_modules/.bin/pnpm --filter @paperclipai/server dev
```
`chmod +x /root/paperclip/run-kobaco.sh`

### 4. Create Systemd Service
Create `/etc/systemd/system/kobaco.service` (Points to the wrapper script):

```ini
[Unit]
Description=Kobaco Paperclip Server
After=docker.service
Wants=docker.service

[Service]
Type=simple
WorkingDirectory=/root/paperclip
# Wrapper script solves PATH and Dynamic IP issues
ExecStart=/bin/bash /root/paperclip/run-kobaco.sh
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 5. Activate
```bash
systemctl daemon-reload
systemctl enable --now kobaco
```

## Troubleshooting
- **502 Error:** Ensure `kobaco-paperclip-1` container is **stopped**. It blocks port 3200.
- **Connection Refused:** If the DB changes IP, simply `systemctl restart kobaco`. The script will find the new IP.
- **Systemd Fails (Exit 127):** Verify node is at `/root/.hermes/node/bin/node`.
- **Logs:** `journalctl -u kobaco -f`.