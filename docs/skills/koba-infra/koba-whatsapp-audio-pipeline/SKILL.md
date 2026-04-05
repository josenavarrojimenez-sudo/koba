---
name: koba-whatsapp-audio-pipeline
category: koba-infra
description: Setup and manage the infrastructure for Koba to receive, transcribe, and respond to WhatsApp voice messages via ElevenLabs Scribe and Cloudflare Tunnel. Includes remote autonomy mode (Exec API).
---

# Koba WhatsApp Audio Pipeline

## Architecture
SINGLE path — Hermes native only. **NO OpenClaw references allowed**.

**CRITICAL: Audio Watch Directory**
*   Audio files arrive at: `/root/.hermes/audio_cache/` (NOT `/root/.hermes/cache/audio/`)
*   Outbound files saved to: `/root/.hermes/audio_inbound/`
*   If daemon shows "Seeded 0" but not transcribing, verify `WATCH_DIR` in script matches the actual path where `.ogg` files appear.

```
Jose (WhatsApp) -> Voice Message -> Hermes Bridge -> /root/.hermes/audio_cache/*.ogg
                                                                                   ↓
Koba Audio Daemon v8 (/opt/koba_audio_daemon.py) → Watches /root/.hermes/audio_cache/
                                                                                   ↓
Sends OGG directly to ElevenLabs Scribe V1 -> Writes .txt to same dir + /root/.hermes/audio_inbound/
                                                                                   ↓
Built-in HTTP Bridge (:9999) → Cloudflare Tunnel (audio-koba.cornelio.app)
                                                                                   ↓
Koba reads https://audio-koba.cornelio.app/latest for transcriptions
```

## Components

### 1. Audio Daemon + Bridge (`/opt/koba_audio_daemon.py`) — v8
Python script running on VPS Host. Combines daemon, bridge, and **Remote Execution**.
*   **Watches:** `/root/.hermes/audio_cache/`
*   **Outbound:** `/root/.hermes/audio_inbound/`
*   **Bridge:** Port 9999
*   **Dependencies:** `python3-requests` (installed via `apt install -y python3-requests`)

## CRITICAL API DETAILS (Hard-won)
The ElevenLabs STT API **fails** with 400 or 422 unless:
*   **Field Name:** Must be `file` in the multipart upload (NOT `audio`, NOT `speech`).
*   **Model ID:** Must use `scribe_v1` (v2 fails with 422).
*   **Format:** Raw `.ogg` from WhatsApp works; no ffmpeg conversion needed.
*   **Code Example:** `files={"file": (fn, f, "audio/ogg")}, data={"model_id": "scribe_v1"}`

## Remote Command Execution (Autonomy Mode)
Daemon v8 exposes `POST /exec` on port 9999.

### ⚠️ CRITICAL Auth Format (hard-won fix)
The bridge uses **`k`** and **`c`** keys — NOT `secret`/`command`/`body` parameters.
Using wrong key names returns HTTP 401 or 500.

```json
{"k": "limon8080", "c": "your_bash_command_here"}
```

Content-Type must be `application/json`. This is the ONLY working format.

### From Koba sandbox (Python):
```python
import urllib.request, json
data = json.dumps({"k": "limon8080", "c": "echo hello"}).encode()
req = urllib.request.Request("https://audio-koba.cornelio.app/exec", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=15)
print(resp.read().decode())
```

This allows Koba to manage the VPS (create agents, check logs, restart services) without user intervention.

## Database Access
`psql` is NOT installed on the Host. Always use docker exec:
`docker exec kobaco-db psql -U paperclip -d paperclip -c "SQL_HERE"`

## Troubleshooting
*   **Daemon Dead:** `ps aux | grep koba`. Restart: `nohup python3 -u /opt/koba_audio_daemon.py > /var/log/koba_daemon_v7.log 2>&1 &`.
*   **Transcription Fail:** Check `/var/log/koba_daemon_v7.log`. 400 Error = Wrong field name (use 'file'). 422 Error = Wrong model (use 'scribe_v1').
*   **Hermes Local Fail:** System always tries local Whisper first. Ignore "Invalid model size" errors; Daemon v8 handles it via the Bridge.