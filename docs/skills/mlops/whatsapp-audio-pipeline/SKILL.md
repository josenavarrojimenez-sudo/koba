---
name: whatsapp-audio-pipeline
description: Complete pipeline for transcribing WhatsApp voice messages and generating audio responses. Monitors OpenClaw's inbound audio directory, transcribes via ElevenLabs Scribe V2, saves transcriptions to Koba's directories for the agent to read, and generates OGG Opus responses for WhatsApp.
category: mlops
---

# WhatsApp Audio Pipeline

Complete pipeline for transcribing WhatsApp voice messages from OpenClaw and generating audio responses via ElevenLabs.

## Architecture

```
José → WhatsApp → OpenClaw daemon (downloads inbound audio)
    → /home/node/.openclaw/media/inbound/*.ogg
    → Koba Audio Daemon (polls every 2s)
    → Copy audio from container to host via docker cp
    → Transcribe via ElevenLabs Scribe V2 API
    → Save transcription to /home/node/.hermes/audio_inbound/*.txt + LATEST_TRANSCRIPTION.json
    → Koba reads transcription → responds
    → Optional: Generate audio response via ElevenLabs TTS
    → Save to /home/node/.hermes/audio_outbound/*.ogg
```

## Prerequisites

- OpenClaw container running with WhatsApp connected (`openclaw-l64u-openclaw-1`)
- ElevenLabs API key (for Scribe V2 STT and Toño TTS)
- Python 3 available on the host
- Docker CLI available on the host

## Setup

### 1. Audio Daemon (Host-side, persistent)

Save to `/opt/koba_audio_daemon.py` and run via `nohup`:

```python
#!/usr/bin/env python3
import os, sys, time, json, subprocess

CONTAINER = 'openclaw-l64u-openclaw-1'
INBOUND = '/home/node/.openclaw/media/inbound'
SEEN = set()
API_KEY = 'YOUR_ELEVENLABS_KEY'
TRANS_DIR = '/home/node/.hermes/audio_inbound'
OUTBOUND_DIR = '/home/node/.hermes/audio_outbound'
LATEST_FILE = '/home/node/.hermes/audio_inbound/LATEST_TRANSCRIPTION.json'

def run_cmd(cmd, timeout=10):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def log(msg):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def list_audio():
    out, _ = run_cmd(f"docker exec {CONTAINER} bash -c 'ls {INBOUND}/*.ogg 2>/dev/null'")
    return [f for f in out.split('\n') if f.strip()] if out else []

def copy_out(container_path):
    ext = int(time.time() * 1000)
    host_tmp = f"/tmp/koba_audio_{ext}.ogg"
    run_cmd(f"docker cp {CONTAINER}:'{container_path}' {host_tmp}", timeout=15)
    return host_tmp if os.path.exists(host_tmp) else None

def transcribe(local_path):
    r = subprocess.run(
        ['curl','-s','-X','POST','https://api.elevenlabs.io/v1/speech-to-text',
         '-H',f'xi-api-key: {API_KEY}','-F','model_id=scribe_v2',
         '-F','language_code=es','-F',f'file=@{local_path}','-F','num_speakers=1'],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode == 0:
        try:
            data = json.loads(r.stdout)
            text = data.get('text','').strip()
            if text:
                log(f"OK: {text}")
                return text
        except:
            pass
    log("STT FAIL")
    return None

def save(text, audio_name):
    os.makedirs(TRANS_DIR, exist_ok=True)
    tfile = os.path.join(TRANS_DIR, audio_name.replace('.ogg','.txt'))
    data = {'text': text, 'ts': time.time(), 'audio': audio_name}
    with open(tfile, 'w') as f:
        json.dump(data, f, indent=2)
    with open(LATEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return tfile

def main():
    os.makedirs(TRANS_DIR, exist_ok=True)
    os.makedirs(OUTBOUND_DIR, exist_ok=True)
    log("=== Koba Audio Daemon ===")
    existing = list_audio()
    SEEN.update(existing)
    log(f"Tracking {len(SEEN)} existing files")
    log("Listening for new audio...")
    while True:
        try:
            current = list_audio()
            new = [f for f in current if f not in SEEN]
            for f in new:
                SEEN.add(f)
                log(f"NEW AUDIO: {os.path.basename(f)}")
                local = copy_out(f)
                if local:
                    text = transcribe(local)
                    if text:
                        save(text, os.path.basename(f))
                    try:
                        os.unlink(local)
                    except:
                        pass
                time.sleep(1)
            time.sleep(2)
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(3)

if __name__ == '__main__':
    main()
```

### 2. Start the Daemon

```bash
chmod +x /opt/koba_audio_daemon.py
nohup python3 /opt/koba_audio_daemon.py > /tmp/koba_audio_daemon.log 2>&1 < /dev/null &

# Verify
ps aux | grep koba_audio_daemon | grep -v grep
cat /tmp/koba_audio_daemon.log | tail -10

# Add to crontab for reboot persistence
(crontab -l 2>/dev/null; echo "@reboot nohup python3 /opt/koba_audio_daemon.py >> /tmp/koba_audio_daemon.log 2>&1") | crontab -
```

### 3. TTS (Text → Audio for WhatsApp)

```bash
#!/bin/bash
# tts_opus_whatsapp.sh
TEXT="$1"
OUTPUT="${2:-/tmp/respuesta.ogg}"
VOICE="iwd8AcSi0Je5Quc56ezK"  # Toño voice
API_KEY="YOUR_ELEVENLABS_KEY"

curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/${VOICE}?output_format=opus_48000_64" \
  -H "xi-api-key: ${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"${TEXT}\"}" \
  -o "$OUTPUT"

if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
    SIZE=$(stat -c%s "$OUTPUT" 2>/dev/null || stat -f%z "$OUTPUT" 2>/dev/null)
    echo "Audio: $OUTPUT ($SIZE bytes)"
else
    echo "ERROR: TTS failed" >&2
    exit 1
fi
```

### 4. Send Audio Response via OpenClaw

```bash
openclaw message send --channel whatsapp --to +50672516680 --media /home/node/.hermes/audio_outbound/respuesta.ogg
```

## Key Directories

| Directory | Purpose | Owner |
|-----------|---------|-------|
| `/home/node/.openclaw/media/inbound/` | WhatsApp inbound audio (container) | OpenClaw |
| `/home/node/.hermes/audio_inbound/` | Transcription files (*.txt + LATEST_TRANSCRIPTION.json) | Koba |
| `/home/node/.hermes/audio_outbound/` | Generated TTS responses (*.ogg) | Koba |
| `/opt/koba_audio_daemon.py` | Audio monitoring daemon | Koba |
| `/tmp/koba_audio_daemon.log` | Daemon logs | Koba |

## Audio API Reference (ElevenLabs)

| Operation | Endpoint | Format |
|-----------|----------|--------|
| STT | `POST /v1/speech-to-text` | model_id=scribe_v2, language_code=es |
| TTS | `POST /v1/text-to-speech/{voice_id}` | output_format=opus_48000_64 |

**Voice IDs:**
- Toño (TTS): `iwd8AcSi0Je5Quc56ezK`

## Troubleshooting

### "WhatsApp cycling with status 499"
- WhatsApp Web disconnects every ~1 minute. Restart: `docker restart openclaw-l64u-openclaw-1`
- Check: `docker logs openclaw-l64u-openclaw-1 --tail 20 | grep -i whatsapp`

### "Audio not arriving to inbound"
- Voice messages sometimes don't download when WhatsApp reconnects after 499
- Fix: Restart OpenClaw container to get fresh connection
- Verify: `docker exec openclaw-l64u-openclaw-1 bash -c 'ls -lt /home/node/.openclaw/media/inbound/*.ogg'`

### "Daemon not picking up new files"
- Check: `cat /tmp/koba_audio_daemon.log | tail -20`
- Restart: `pkill -f koba_audio_daemon && nohup python3 /opt/koba_audio_daemon.py > /tmp/koba_audio_daemon.log 2>&1 &`
- The daemon uses `docker exec` to list files and `docker cp` to copy them

### "Transcription fails"
- Check: `ls -la /home/node/.hermes/audio_inbound/LATEST_TRANSCRIPTION.json`
- Manual test: Copy audio to host and curl the ElevenLabs API directly

## Rule 2.5

**Audio → Audio / Text → Text (Reciprocidad modal completa)**
- If user sends voice message → Koba MUST respond with voice (TTS via Toño)
- If user sends text → Koba responds with text
- Never break this rule