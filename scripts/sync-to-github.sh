#!/bin/bash
# Koba Repo Sync Script - Updates all .md files from live sources and pushes to GitHub
set -e

REPO_DIR="/root/koba"
cd "$REPO_DIR"

echo "=== Syncing Koba Repo ==="

# 1. Update SOUL.md from live source
if [ -f /root/.hermes/soul.md ]; then
    cp /root/.hermes/soul.md "$REPO_DIR/SOUL.md"
    echo "[OK] Updated SOUL.md from /root/.hermes/soul.md"
fi

# 2. Pull latest changes (in case of remote updates)
git pull --rebase origin main 2>/dev/null || true

# 3. Stage, commit, push
git add -A
if git diff --cached --quiet; then
    echo "[OK] No changes detected. Nothing to commit."
else
    git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M UTC')"
    git push origin main
    echo "[OK] Changes pushed to GitHub"
fi

echo "=== Sync Complete ==="
