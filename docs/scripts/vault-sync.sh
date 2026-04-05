#!/bin/bash
cd /root/koba/vault

# Pull any changes from Jose
git pull --rebase origin main 2>/dev/null || true

# Add and push any changes from agents
git add -A
if git diff --cached --quiet; then
    echo "[$(date)] No changes" >> /var/log/koba_vault_sync.log
else
    git commit -m "$(date '+%Y-%m-%d %H:%M') - auto-sync from agents"
    git push origin main
    echo "[$(date]] Pushed changes" >> /var/log/koba_vault_sync.log
fi

