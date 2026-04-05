---
name: hermes-audio-bridge-setup
category: mlops
description: Setup the infrastructure to bridge WhatsApp voice messages from the VPS host to the Hermes Agent. Audio files land in /root/.hermes/audio_cache/, daemon transcribes via ElevenLabs Scribe V2 and saves to /root/.hermes/audio_inbound/. HTTP bridge on port 9999.
---

# Hermes Audio Bridge Setup

**Problem:** Hermes Agent receives WhatsApp voice messages as .ogg files but lacks built-in Whisper models for transcription. The system error "(Local transcription failed: Invalid model size 'whisper-1')" appears when Hermes tries to transcribe without proper model setup.

**Solution:** Host-based daemon pattern:
1.  **Audio arrival:** WhatsApp gateway saves .ogg to `/root/.hermes/audio_cache/`
2.  **Daemon (v4):** Watches cache dir, sends new files to ElevenLabs Scribe API, saves transcription
3.  **Bridge (HTTP):** Serves transcriptions via port 9999
4.  **Tunnel:** Cloudflare routes `audio-koba.cornelio.app` -> `localhost:9999`

## Architecture

```
WhatsApp -> Audio (.ogg) -> /root/.hermes/audio_cache/
                                      |
                              koba_v4.py (daemon)
                                      |
                          ElevenLabs Scribe V2 API
                                      |
                          /root/.hermes/audio_inbound/{hash}.txt
                                      |
                          HTTP Bridge :9999 (builtin to daemon)
                                      |
                          Cloudflare Tunnel -> Agent fetches
```

## 1. The Audio Daemon (koba_v4.py)

**Location:** `/root/koba_v4.py`

```python
#!/usr/bin/env python3
"""Koba Audio Daemon v4 - Clean, no OpenClaw, ElevenLabs Scribe V2"""
import os, glob, requests, time, threading, logging
from http.server import HTTPServer, BaseHTTPRequestHandler

WATCH = "/root/.hermes/audio_cache/"
SAVE = "/root/.hermes/audio_inbound/"
API = os.environ.get("ELEVENLABS_API_KEY", "YOUR_KEY_HERE")
PORT = 9999
LOG = "/var/log/koba_v4.log"

os.makedirs(SAVE, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', 
                    handlers=[logging.FileHandler(LOG), logging.StreamHandler()])
log = logging.getLogger()
SEEN = set()

def process(f):
    log.info(f"Processing {os.path.basename(f)}")
    try:
        # CRITICAL: Use 'audio' as field name, include model_id in data
        with open(f, 'rb') as fh:
            r = requests.post("https://api.elevenlabs.io/v1/speech-to-text",
                              headers={'xi-api-key': API},
                              files={'audio': (os.path.basename(f), fh, 'audio/ogg')},
                              data={'model_id': 'scribe_v2'},
                              timeout=120)
        if r.ok:
            txt = r.json().get('text', '?').strip()
            log.info(f"Result: {txt[:80]}")
            out_path = os.path.join(SAVE, os.path.basename(f).replace('.ogg', '.txt'))
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write(txt)
        else:
            log.error(f"API Error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.error(f"Error: {e}")

def watch_loop():
    log.info(f"Watching {WATCH}")
    log.info("Listening...")
    while True:
        for f in glob.glob(os.path.join(WATCH, "*.ogg")):
            if f not in SEEN:
                SEEN.add(f)
                threading.Thread(target=process, args=(f,), daemon=True).start()
        time.sleep(1)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *a): pass

thread = threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthHandler).serve_forever(), daemon=True)
thread.start()
log.info("Bridge started")
watch_loop()
```

### Deploy & Run
```bash
chmod +x /root/koba_v4.py
pkill -f koba_audio; pkill -f bridge.js
nohup python3 -u /root/koba_v4.py >> /var/log/koba_v4.log 2>&1 &
tail -f /var/log/koba_v4.log
```

### Verify
```bash
# Check daemon is watching correct dir (no OpenClaw references)
tail -n 3 /var/log/koba_v4.log
# Should say: Watching /root/.hermes/audio_cache/ and Listening...

# Check bridge responds
curl -s http://localhost:9999/health
# Should say: OK
```

## 2. Dependencies

```bash
# Must have
python3 -c "import requests"  # Pre-installed on Ubuntu
sudo apt install -y python3-requests

# ffmpeg for audio conversion (if needed)
sudo apt install -y ffmpeg
```

## 3. ElevenLabs API Details

**Endpoint:** `https://api.elevenlabs.io/v1/speech-to-text`

**Required fields:**
- Header: `xi-api-key: YOUR_KEY`
- File field name: **`audio`** (NOT `file`, NOT `voice`)
- Data field: `model_id: scribe_v2`

**Common errors:**
- `400 Must provide either file or a URL` → Wrong field name use `audio` not `file`
- `422 model_id required` → Must include `model_id` in `data` dict
- `401 Unauthorized` → Invalid API key
- Empty transcription → Audio too short/silent

**Available models:** `scribe_v1`, `scribe_v2` (recommended)

## 4. Cloudflare Tunnel

Existing tunnel: `2a1e9aa4-d556-4c90-a1ce-6a461720eb8e` (koba)
Routes: `audio-koba.cornelio.app` -> `localhost:9999`

## 5. Agent Usage

To read transcriptions:
```python
import os, glob
# Check for new transcriptions
for f in sorted(glob.glob("/root/.hermes/audio_inbound/*.txt")):
    with open(f) as fh:
        print(f"{f}: {fh.read()[:100]}")
```

To trigger transcription manually (for a specific file):
```bash
python3 -c "
import os, requests
api = 'YOUR_ELEVEN_KEY'
path = '/root/.hermes/audio_cache/test.ogg'
with open(path, 'rb') as f:
    r = requests.post('https://api.elevenlabs.io/v1/speech-to-text',
                      headers={'xi-api-key': api},
                      files={'audio': ('audio.ogg', f, 'audio/ogg')},
                      data={'model_id': 'scribe_v2'},
                      timeout=120)
print(r.status_code, r.text[:200])
"
```

## 6. File Locations Summary

| Component | Path |
|-----------|------|
| Daemon script | `/root/koba_v4.py` |
| Audio cache (inbound .ogg) | `/root/.hermes/audio_cache/` |
| Transcriptions (output .txt) | `/root/.hermes/audio_inbound/` |
| Daemon log | `/var/log/koba_v4.log` |
| HTTP Bridge | Port 9999 |

## Pitfalls

1. **OpenClaw references:** NEVER use OpenClaw container paths. The daemon watches the HOST directory where WhatsApp gateway saves files.
2. **Daemon gets killed on reboot:** Add to systemd or crontab `@reboot`:
   ```bash
   @reboot sleep 10 && nohup python3 -u /root/koba_v4.py >> /var/log/koba_v4.log 2>&1 &
   ```
3. **Old logs mislead:** The log file APPENDS, so old "Listening..." messages appear before new ones. Always check timestamps and `tail` after restarting.
4. **Multiple daemons:** Use `pkill -f koba_v4` or `pkill -f koba_audio` before starting new one. Multiple daemons = duplicate processing.
5. **ElevenLabs field name:** Must be `audio` (not `file`, not `voice`, not `audio_file`). The `model_id` must be in the `data` parameter, not headers.
6. **SEEN set is in-memory:** If daemon restarts, it reprocesses ALL existing .ogg files. Clean cache before restart if you don't want duplicates.