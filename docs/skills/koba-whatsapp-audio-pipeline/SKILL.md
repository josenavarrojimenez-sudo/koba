---
name: koba-whatsapp-audio-pipeline
category: koba-infra
description: Setup and manage the infrastructure for Koba to receive, transcribe, and respond to WhatsApp voice messages via ElevenLabs Scribe and Cloudflare Tunnel.
---

# Koba WhatsApp Audio Pipeline

## Architecture
SINGLE path — Hermes native only. **NO OpenClaw references allowed** (user explicitly banned OpenClaw).

```
Jose (WhatsApp) -> Voice Message -> Hermes Baileys Bridge -> /root/.hermes/audio_cache/*.ogg
                                                                                    ↓
Koba Audio Daemon v5 (VPS Host /opt/koba_audio_daemon.py) → Watches /root/.hermes/audio_cache/
                                                                                    ↓
Sends OGG directly to ElevenLabs Scribe V1 -> Writes .txt to /root/.hermes/audio_inbound/{name}.txt
                                                                                    ↓
Built-in HTTP Bridge (:9999) → Cloudflare Tunnel (audio-koba.cornelio.app)
                                                                                    ↓
Koba reads https://audio-koba.cornelio.app/latest
```

**CRITICAL:** The Daemon watches ONLY `/root/.hermes/audio_cache/`. Never reference OpenClaw paths or containers.

## Components

### 1. Audio Daemon + Bridge (`/opt/koba_audio_daemon.py`) — v5
Python script running on the Host VPS as systemd service (`koba-daemon.service`). **Combines daemon + bridge in one script.**
*   **Role:** Monitors `/root/.hermes/audio_cache/` for new `.ogg` files.
*   **Mechanism:** Detects new file -> Sends OGG **directly** to ElevenLabs (no ffmpeg needed!) -> Writes transcription to `/root/.hermes/audio_inbound/{name}.txt`.
*   **HTTP Bridge:** Built-in, serves on port 9999:
    *   `/health` — Returns `{"status": "alive", "version": "v5"}`
    *   `/latest` — Returns most recent transcription as JSON
    *   `/transcriptions` — Returns all transcriptions as JSON
*   **Persistence:** systemd service `koba-daemon.service` (survives reboots).
*   **Dependencies:** `python3-requests`, `ffmpeg` (both pre-installed on VPS, though ffmpeg is no longer needed for STT).
*   **API Key:** ElevenLabs key hardcoded in script.

### 2. Cloudflare Configuration
*   **Tunnel:** `koba` (ID: `2a1e9aa4-d556-4c90-a1ce-6a461720eb8e`).
*   **Routes:**
    *   `audio-koba.cornelio.app` -> `http://localhost:9999`
    *   `kobaco.cornelio.app` -> `localhost:3200`

## CRITICAL ELEVENLABS API DETAILS (learned through trial and error)

The ElevenLabs Speech-to-Text API **requires** these exact parameters:
*   **URL:** `https://api.elevenlabs.io/v1/speech-to-text`
*   **Header:** `xi-api-key: <key>`
*   **Files field name:** Must be `'file'` (NOT `'audio'` — ElevenLabs will return 400 "Must provide either file or a URL parameter")
*   **Data:** `{'model_id': 'scribe_v1'}` (NOT `scribe_v2` — returns 422 "Field required")
*   **Audio format:** OGG works directly, **no ffmpeg conversion needed**
*   **Working example:**
```python
with open(path, 'rb') as f:
    r = requests.post('https://api.elevenlabs.io/v1/speech-to-text',
                      headers={'xi-api-key': API_KEY},
                      files={'file': ('audio.ogg', f, 'audio/ogg')},
                      data={'model_id': 'scribe_v1'},
                      timeout=120)
```

## Start/Stop/Restart (systemd)

### Check status
```bash
sudo systemctl status koba-daemon --no-pager -l
tail -n 15 /var/log/koba_daemon_v5.log
```

### Restart
```bash
sudo systemctl restart koba-daemon
```

### Stop
```bash
sudo systemctl stop koba-daemon
```

### Manual start (fallback if systemd fails)
```bash
nohup python3 -u /opt/koba_audio_daemon.py >> /var/log/koba_daemon_v5.log 2>&1 &
```

### Verify
```bash
tail -n 5 /var/log/koba_daemon_v5.log
# Must say: "=== Koba Audio Daemon v5 ===", "Listening...", "Bridge on http://0.0.0.0:9999"
curl -s http://localhost:9999/health
# Must say: {"status": "alive", "version": "v5"}
```

## GitHub Repository

All Koba `.md` files are maintained in:
*   **Repo:** `https://github.com/josenavarrojimenez-sudo/koba`
*   **Owner:** `josenavarrojimenez-sudo`
*   **Tools:** `gh` CLI (installed in `/usr/local/bin/gh`)
*   **Auth:** GitHub PAT token

### Structure
```
koba/
├── SOUL.md                 # Identidad y reglas de Koba
├── README.md               # Overview del proyecto
├── docs/
│   ├── infra.md            # Documentacion tecnica de infraestructura
│   └── inmortales.md       # Reglas del grupo WhatsApp Inmortales
└── scripts/
    ├── koba-health.sh      # Health check del sistema
    └── README.md
```

### Update repo from VPS
```bash
cd /root/koba
git add -A
git commit -m "Update $(date +%Y-%m-%d)"
git push origin main
```

### Create repo (if needed again)
```bash
gh repo create josenavarrojimenez-sudo/koba --public --clone
```

## Health Check Script

A manual health check script exists at `/opt/koba_health_check.sh`. Run it for a quick status:
```bash
bash /opt/koba_health_check.sh
# Or use the scripts/koba-health.sh from the repo
```

## Troubleshooting

### 403 Forbidden (WAF Block)
*   **Symptom:** Koba sees `HTTP 403` when accessing the bridge URL.
*   **Fix:** Cloudflare Dashboard > Security > WAF > Create rule to Skip for Hostname `audio-koba.cornelio.app`.

### Audio Not Being Transcribed
*   **Check:**
    1.  Daemon alive? `sudo systemctl status koba-daemon`
    2.  Log shows listening? `tail /var/log/koba_daemon_v5.log`
    3.  Audio file in cache? `ls -lt /root/.hermes/audio_cache/*.ogg | head -3`
    4.  Bridge responding? `curl -s http://localhost:9999/health`
    5.  Transcription saved? `ls -lt /root/.hermes/audio_inbound/*.txt`

### Script got corrupted/deleted
*   **Symptom:** `ls /opt/koba_audio_daemon.py` returns nothing.
*   **Fix:** Recreate the file entirely. Key config values:
    *   `ELEVENLABS_API_KEY = "b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea"`
    *   `WATCH_DIR = "/root/.hermes/audio_cache/"`
    *   `OUT_DIR = "/root/.hermes/audio_inbound/"`
    *   `BRIDGE_PORT = 9999`
    *   ElevenLabs field must be `'file'`, model `'scribe_v1'`

### `sed` corrupted the script
*   **PITFALL:** Using `sed` to replace long paths in the daemon script caused duplication/corruption. If the script is corrupted, **rewrite it entirely** using python3 heredoc or direct file write.

### systemd runs old/wrong script
*   **Symptom:** Logs show wrong version or OpenClaw references after update.
*   **Fix:** `sudo systemctl stop koba-daemon`, verify `/opt/koba_audio_daemon.py` has correct content, then `sudo systemctl daemon-reload && sudo systemctl start koba-daemon`

## WhatsApp Group Rules (Inmortales)
- **Jose** (+50672516680): Respond every time he asks something or adds value.
- **Bachi** (+50688218905): Respond if you can add value to the conversation.
- **Cornelio** (+50664127309): Another personal AI agent. Max 6 consecutive messages to avoid loops.
- **Silence Rule:** If a message ONLY names Cornelio, Bachi, or Jose (not Koba) → Koba stays silent. Only speak when directly asked, tagged, or adding clear value.
- **Modality:** Audio → Audio response, Text → Text response (Rule 2.5 — sacred, never break).
- Emojis OK, tone: compas/amigos.
