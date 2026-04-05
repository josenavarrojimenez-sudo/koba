#!/bin/bash
# Koba Audio System Health Check
echo "=== Koba Audio Daemon Status ==="
systemctl status koba-daemon --no-pager -l 2>/dev/null || echo "[WARN] systemd unavailable"
echo ""
echo "=== Bridge Health ==="
curl -s --max-time 5 http://localhost:9999/health || echo "[FAIL] Bridge down"
echo ""
echo "=== Recent Transcriptions ==="
ls -lt /root/.hermes/audio_inbound/*.txt 2>/dev/null | head -5 || echo "[INFO] None yet"
echo ""
echo "=== Last 10 log lines ==="
tail -n 10 /var/log/koba_daemon_v5.log 2>/dev/null || echo "[WARN] No logs"
