---
name: koba-whatsapp-voice-return
description: Pipeline to generate and send native WhatsApp voice notes (OGG Opus) via ElevenLabs (Toño) when Hermes TTS fails or for manual requests.
category: koba-infra
---

# Koba WhatsApp Voice Return Pipeline

## Context
Hermes' built-in TTS often delivers MP3 links or fails to send native `.ogg` voice notes to WhatsApp because the bridge requires OGG Opus via the `/send-media` endpoint. This skill provides a reliable workaround to deliver **native voice notes**.

## Prerequisites
- **Script location:** `/root/koba/scripts/koba_tts_whatsapp.py`
- **ElevenLabs API Key:** Stored in `/root/.hermes/.env` (`ELEVENLABS_API_KEY`).
- **Voice ID:** Toño (`iwd8AcSi0Je5Quc56ezK`).
- **Bridge:** WhatsApp bridge running on port `3000`.
- **FFmpeg:** Installed at `/usr/bin/ffmpeg`.

## How it works
1. **TTS Request:** Python script calls ElevenLabs API directly.
2. **Conversion:** `ffmpeg` converts the MP3 response to **OGG Opus** (voip settings).
3. **Delivery:** Sends the file to the WhatsApp bridge `/send-media` endpoint as a voice note (`ptt: true`).

## Execution via Bridge
Since I cannot execute local scripts directly if Hermes TTS is broken, use the remote bridge.

**Bridge Secret:** `limon8080`
**Endpoint:** `https://audio-koba.cornelio.app/exec`
**Auth Keys:** Body must use `"k"` (key) and `"c"` (command).

### Command Template
```python
import urllib.request
import json

bridge_url = "https://audio-koba.cornelio.app/exec"
secret = "limon8080"

# The text you want to convert to voice
text = "Hola Jefe, aquí tu mensaje."

# Construct the shell command to trigger the pipeline
script_path = "/root/koba/scripts/koba_tts_whatsapp.py"
chat_id = "50672516680@s.whatsapp.net" # Default for Jose
shell_cmd = f"export ELEVENLABS_API_KEY=$(grep '^ELEVENLABS_API_KEY=' /root/.hermes/.env | cut -d= -f2) && python3 {script_path} '{text}' {chat_id}"

payload = json.dumps({"k": secret, "c": shell_cmd}).encode()
req = urllib.request.Request(bridge_url, data=payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req, timeout=60)
print(resp.read().decode())
```

## Key Technical Details (Verified)

### Bridge `/send-media` Endpoint
The WhatsApp bridge at port 3000 accepts media at `POST /send-media`:
```json
{
  "chatId": "50672516680@s.whatsapp.net",
  "filePath": "/root/.hermes/audio_outbound/koba_20260405_132659.ogg",
  "mediaType": "audio",
  "caption": "optional"
}
```
- Detects `.ogg`/`.opus` extension automatically and sets `ptt: true` (voice note mode).
- Returns `{"success": true, "messageId": "..."}` on success.

### STT Configuration Fix (Critical)
In `~/.hermes/config.yaml`, the `stt:` section must NOT have a stray top-level `model:` line. Wrong:
```yaml
stt:
  provider: local
  local:
    model: base
  openai:
    model: whisper-1
  model: whisper-1  # <-- THIS STRAY LINE OVERRIDES LOCAL MODEL AND BREAKS STT
```
Remove the stray `model: whisper-1` so only `local.model: base` applies.

### Daemon Info
- **Audio/Exec Bridge:** `python3 /opt/koba_audio_daemon.py` on port 9999
- **Health endpoint:** `https://audio-koba.cornelio.app/health`
- **WhatsApp Bridge:** `node .../whatsapp-bridge/bridge.js --port 3000`
- **Voice:** Toño ID = `iwd8AcSi0Je5Quc56ezK`
- **FFmpeg:** `/usr/bin/ffmpeg` with `libopus` encoder

## Troubleshooting
- **404 on /exec:** Check daemon: `ps aux | grep koba_audio_daemon`. Restart: `systemctl restart koba-audio` or manual: `nohup python3 /opt/koba_audio_daemon.py &`
- **401 on /exec:** Auth uses `"k"` for key and `"c"` for command in JSON body. Key = `limon8080`.
- **STT fails (Invalid model):** Check `~/.hermes/config.yaml` — remove any stray `model: whisper-1` under `stt:`, ensure `provider: local` and `local.model: base`.
- **faster-whisper missing:** Install in gateway venv: `cd /root/.hermes/hermes-agent && venv/bin/pip install faster-whisper`
- **ElevenLabs Error:** `grep ELEVENLABS_API_KEY /root/.hermes/.env`
- **Bridge not sending voice notes:** Ensure file extension is `.ogg` (not `.mp3`) and bridge is on port 3000: `curl http://127.0.0.1:3000/health`
