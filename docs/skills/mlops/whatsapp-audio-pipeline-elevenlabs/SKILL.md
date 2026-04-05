---
name: whatsapp-audio-pipeline-elevenlabs
description: Complete WhatsApp voice message pipeline — inbound audio from OpenClaw → ElevenLabs Scribe V2 transcription → AI response → ElevenLabs TTS → OGG Opus outbound → WhatsApp delivery.
category: mlops
---

# WhatsApp Audio Pipeline (ElevenLabs + OpenClaw)

**Trigger:** Voice messages arrive via WhatsApp on OpenClaw gateway — need automatic STT (Spanish) and TTS (OGG Opus) response for Rule 2.5 compliance.

## Architecture

```
Jose voice msg → WhatsApp → OpenClaw gateway
                                    ↓
                    /home/node/.openclaw/media/inbound/{uuid}.ogg
                                    ↓
                    Koba Audio Daemon (polls every 2s via docker exec)
                                    ↓
                    docker cp + ElevenLabs Scribe V2 API
                                    ↓
                    /home/node/.hermes/audio_inbound/{uuid}.txt (transcription)
                                    ↓
                    AI processes transcription → generates response
                                    ↓
                    ElevenLabs TTS → OGG Opus
                                    ↓
                    /home/node/.hermes/audio_outbound/respuesta.ogg
                                    ↓
                    openclaw message send → Jose WhatsApp
```

## Key Directories (Host)

| Path | Purpose |
|------|---------|
| `/home/node/.openclaw/media/inbound/` | OpenClaw saves inbound media (audio/images) |
| `/home/node/.hermes/audio_inbound/` | Saved transcriptions (.txt with metadata) |
| `/home/node/.hermes/audio_outbound/` | Generated TTS audio (OGG Opus) |
| `/opt/koba_audio_daemon.py` | Daemon script (persistent) |
| `/tmp/koba_audio_daemon.log` | Daemon log file |

## Audio Daemon

### Location: `/opt/koba_audio_daemon.py`

The daemon runs as a background Python process on the HOST. It:
1. Uses `docker exec` to poll `/home/node/.openclaw/media/inbound/*.ogg` inside the OpenClaw container
2. Copies new audio files to host via `docker cp`
3. Sends to ElevenLabs Scribe V2 for Spanish transcription
4. Saves result to `/home/node/.hermes/audio_inbound/{name}.txt`

### Daemon Code Pattern

```python
#!/usr/bin/env python3
import os, sys, time, json, subprocess

CONTAINER = 'openclaw-l64u-openclaw-1'
INBOUND = '/home/node/.openclaw/media/inbound'
SEEN = set()
API_KEY = 'b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea'
TRANS_DIR = '/home/node/.hermes/audio_inbound'

def run_cmd(cmd, timeout=10):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def transcribe(local_path):
    r = subprocess.run([
        'curl', '-s', '-X', 'POST',
        'https://api.elevenlabs.io/v1/speech-to-text',
        '-H', f'xi-api-key: {API_KEY}',
        '-F', 'model_id=scribe_v2',
        '-F', 'language_code=es',
        '-F', f'file=@{local_path}',
        '-F', 'num_speakers=1'
    ], capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        data = json.loads(r.stdout)
        return data.get('text', '').strip()
    return None

# Main loop: poll every 2s, check for new .ogg files, copy out, transcribe, save
```

### Starting the Daemon

```bash
nohup python3 /opt/koba_audio_daemon.py > /tmp/koba_audio_daemon.log 2>&1 &
```

### Persistence via Crontab

```bash
(crontab -l 2>/dev/null; echo "@reboot nohup python3 /opt/koba_audio_daemon.py >> /tmp/koba_audio_daemon.log 2>&1") | crontab -
```

## ElevenLabs API Details

### STT (Speech-to-Text)
```bash
curl -s -X POST 'https://api.elevenlabs.io/v1/speech-to-text' \
  -H 'xi-api-key: YOUR_API_KEY' \
  -F 'model_id=scribe_v2' \
  -F 'language_code=es' \
  -F 'file=@audio.ogg' \
  -F 'num_speakers=1'
```

**Response format:**
```json
{
  "text": "Excelente, ahora haceme un sonido de efecto de un trueno",
  "segments": [{"text": "...", "start": 0, "end": 3.5}]
}
```

**IMPORTANT:** Only use model IDs that Scribe V2 accepts: `scribe_v2`, `scribe_v1`, or the standard Whisper models (`large-v3`, `turbo`, etc). Do NOT use `whisper-1` — it causes an error.

### TTS (Text-to-Speech)
```bash
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/iwd8AcSi0Je5Quc56ezK?output_format=opus_48000_64" \
  -H 'xi-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Hola mae, sistema funcionando"}' \
  -o output.ogg
```

**Response:** Raw OGG Opus binary (compatible with WhatsApp)

**Voice ID for Toño:** `iwd8AcSi0Je5Quc56ezK`

## Sending Audio via OpenClaw (WhatsApp)

```bash
openclaw message send \
  --channel whatsapp \
  --to +50672516680 \
  --media /home/node/.hermes/audio_outbound/respuesta.ogg
```

## HOW TO CHECK FOR NEW INBOUND VOICE MESSAGES

### Step 1: Check if a new audio file arrived in OpenClaw
```bash
# List latest inbound audio files
docker exec openclaw-l64u-openclaw-1 bash -c 'ls -lt /home/node/.openclaw/media/inbound/*.ogg 2>/dev/null | head -10'
```

### Step 2: Check if the daemon already transcribed it
```bash
cat /tmp/koba_audio_daemon.log | tail -20
```
If the daemon processed it, you'll see:
```
[HH:MM:SS] NEW: {uuid}.ogg
[HH:MM:SS] STT: koba_audio_{timestamp}.ogg
[HH:MM:SS] OK: {transcription text}
[HH:MM:SS] Saved: /home/node/.hermes/audio_inbound/{uuid}.txt
```

### Step 3: Read the transcription
```bash
cat /home/node/.hermes/audio_inbound/{uuid}.txt
```

### Step 4: If the daemon hasn't picked it up yet, transcribe manually
```bash
# Copy from container to host
docker cp openclaw-l64u-openclaw-1:'/home/node/.openclaw/media/inbound/{uuid}.ogg' /tmp/voice.og

# Transcribe
curl -s -X POST 'https://api.elevenlabs.io/v1/speech-to-text' \
  -H 'xi-api-key: YOUR_KEY' \
  -F 'model_id=scribe_v2' \
  -F 'language_code=es' \
  -F 'file=@/tmp/voice.ogg' \
  -F 'num_speakers=1'
```

## DAEMON VERIFICATION & TROUBLESHOOTING

### Check if daemon is running
```bash
ps aux | grep koba_audio_daemon | grep -v grep
```
Expected: `root PID 0.4 0.0 python3 /opt/koba_audio_daemon.py`

### If daemon is NOT running, restart
```bash
pkill -f koba_audio_daemon 2>/dev/null
sleep 1
nohup python3 /opt/koba_audio_daemon.py > /tmp/koba_audio_daemon.log 2>&1 &
```

### If voice messages not arriving (OpenClaw WA disconnect)
```bash
docker restart openclaw-l64u-openclaw-1
sleep 20
# Wait 30s for WA to reconnect, then re-send voice message
```

## Known Issues & Pitfalls

### 0. Audio Lives INSIDE Container — MUST Use docker exec/cp
CRITICAL: The inbound audio files are inside the `openclaw-l64u-openclaw-1` container at `/home/node/.openclaw/media/inbound/*.ogg`. You CANNOT access them with regular filesystem tools from the host. The daemon uses `docker exec openclaw-l64u-openclaw-1 bash -c 'ls ...'` to list files and `docker cp openclaw-l64u-openclaw-1:/path/to/file /tmp/dest` to download them.

### 1. WhatsApp 499 Loop
OpenClaw's WhatsApp Web connection drops every ~1 minute with status 499:
```
[whatsapp] Web connection closed (status 499). Retry 1/12 in 2s...
[whatsapp] Listening for personal WhatsApp inbound messages.
```
The connection recovers automatically. Media files are still saved during the brief connected windows. Audio files persist in the inbound folder even if delivery fails.

### 2. Audio Files Live Inside OpenClaw Container
The inbound directory is `/home/node/.openclaw/media/inbound/` INSIDE the `openclaw-l64u-openclaw-1` container. The daemon MUST use `docker exec` to list files and `docker cp` to download them — can't mount volumes from managed Docker.

### 3. Voice Messages Arrive as OGG Opus
WhatsApp voice messages are saved as `audio/ogg; codecs=opus`. ElevenLabs Scribe V2 accepts OGG/Opus directly — no conversion needed.

### 4. Channel Conflicts
When sending via OpenClaw CLI with multiple channels configured (WhatsApp + Telegram), you MUST specify `--channel whatsapp` or it fails with:
```
Channel is required when multiple channels are configured: telegram, whatsapp
```

### 5. No Active WhatsApp Listener
If WhatsApp Web is disconnected, sending fails with:
```
Error: No active WhatsApp Web listener (account: default)
```
The connection auto-reconnects. Wait ~30 seconds and retry.

### 6. ElevenLabs STT Model Names
Use ONLY: `scribe_v2` (recommended), `scribe_v1`, or Whisper variants like `large-v3`, `turbo`. The model ID `whisper-1` throws `Invalid model size` error.

### 7. Hermes Sandbox Cannot Receive Audio Files Directly
When a voice message arrives via WhatsApp on the Hermes platform, the agent receives `[audio received]` notification but the actual .ogg file is NOT downloaded to the sandbox. The audio file ONLY arrives on the Hostinger server inside the OpenClaw container at `/home/node/.openclaw/media/inbound/`. The daemon bridges this gap.

### 8. Paramiko Session Resets
SSH sessions reset between commands, losing Python packages. Always `pip install paramiko` before each SSH operation, or use a wrapper script on the host.

## Full Test Flow

```bash
# 1. Verify daemon is running
ps aux | grep koba_audio_daemon | grep -v grep

# 2. Drop a test audio into OpenClaw inbound
docker exec openclaw-l64u-openclaw-1 cp \
  /home/node/.openclaw/media/inbound/existing.ogg \
  /home/node/.openclaw/media/inbound/test_$(date +%s).ogg

# 3. Wait 10s, check daemon log
cat /tmp/koba_audio_daemon.log | tail -10

# 4. Verify transcription
ls -la /home/node/.hermes/audio_inbound/*.txt
cat /home/node/.hermes/audio_inbound/test_*.txt

# 5. Generate TTS response
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/iwd8AcSi0Je5Quc56ezK?output_format=opus_48000_64" \
  -H 'xi-api-key: YOUR_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Pura vida mae, todo funcionando"}' \
  -o /home/node/.hermes/audio_outbound/respuesta.ogg

# 6. Send via OpenClaw
openclaw message send --channel whatsapp --to +50672516680 \
  --media /home/node/.hermes/audio_outbound/respuesta.ogg
```