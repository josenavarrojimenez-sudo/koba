#!/bin/bash
# Koba Repo Sync Script - Updates ALL .md files from live sources and pushes to GitHub
set -e

REPO_DIR="/root/koba"
cd "$REPO_DIR"

echo "=== Syncing Koba Repo ==="
echo "Started: $(date)"

# ============================================================
# 1. Update core files from live sources
# ============================================================

# SOUL.md
if [ -f /root/.hermes/soul.md ]; then
    cp /root/.hermes/soul.md "$REPO_DIR/SOUL.md"
    echo "[OK] Updated SOUL.md"
fi

# Audio Daemon V4/V5 info (just metadata, not the full script)
if pgrep -f "koba_v4" > /dev/null 2>&1 || pgrep -f "koba_audio_daemon" > /dev/null 2>&1 || systemctl is-active koba-daemon > /dev/null 2>&1; then
    echo "[OK] Audio daemon is running"
    cat > "$REPO_DIR/docs/daemon-status.md" << EOF
# Audio Daemon Status
- **Status**: Running (active)
- **Last check**: $(date)
- **Process**: $(pgrep -fa "koba" 2>/dev/null || echo "unknown")
- **Log tail**:
$(tail -n 5 /var/log/koba_daemon_v5.log 2>/dev/null || tail -n 5 /var/log/koba_v4.log 2>/dev/null || echo "No logs found")
EOF
fi

# ============================================================
# 2. Update Kobaco docs
# ============================================================
if [ -f /root/paperclip/run-kobaco.sh ]; then
    cp /root/paperclip/run-kobaco.sh "$REPO_DIR/run-kobaco.sh" 2>/dev/null || true
    echo "[OK] Updated run-kobaco.sh"
fi

# ============================================================
# 3. Copy relevant skills to docs
# ============================================================
mkdir -p "$REPO_DIR/docs/skills/kobaco-systemd-hardening"
mkdir -p "$REPO_DIR/docs/skills/koba-whatsapp-audio-pipeline"
mkdir -p "$REPO_DIR/docs/skills/koba-outbound-audio-bridge-fix"
mkdir -p "$REPO_DIR/docs/skills/kobaco-maintenance"
mkdir -p "$REPO_DIR/docs/skills/paperclip-agent-management"

for skill in kobaco-systemd-hardening koba-whatsapp-audio-pipeline koba-outbound-audio-bridge-fix kobaco-maintenance; do
    src="/root/.hermes/skills/koba-infra/$skill/SKILL.md"
    if [ -f "$src" ]; then
        cp "$src" "$REPO_DIR/docs/skills/$skill/SKILL.md"
        echo "[OK] Updated skill: $skill"
    fi
done

# paperclip agent management
src="/root/.hermes/skills/devops/paperclip-agent-management/SKILL.md"
if [ -f "$src" ]; then
    cp "$src" "$REPO_DIR/docs/skills/paperclip-agent-management/SKILL.md"
    echo "[OK] Updated skill: paperclip-agent-management"
fi

# ============================================================
# 4. Pull, commit, push
# ============================================================
git pull --rebase origin main 2>/dev/null || true

git add -A

if git diff --cached --quiet; then
    echo "[OK] No changes detected."
else
    git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M UTC')"
    git push origin main
    echo "[OK] Changes pushed to GitHub"
fi

echo "=== Sync Complete ==="
