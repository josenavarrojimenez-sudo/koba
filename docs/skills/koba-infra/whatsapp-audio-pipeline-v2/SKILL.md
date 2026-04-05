---
name: whatsapp-audio-pipeline-v2
description: Send native WhatsApp voice notes using ElevenLabs (Toño voice) and the /send-media bridge. Fixes the issue where TTS only returned file paths.
category: koba-infra
---

# WhatsApp Audio Pipeline v2 (Successful Flow)

## Trigger
User sends a voice message on WhatsApp that requires a voice response (or user explicitly asks for an audio response).

## Rules (Sacrosanct)
1.  **Reciprocity:** Audio Input → Audio Output. Text Input → Text Output.
2.  **NEVER** return a file path (e.g., `file:///...`) or a URL.
3.  **NEVER** use the generic `text_to_speech` tool for WhatsApp (it fails to send as a PTT/note).
4.  **Always** use the specific script execution flow defined below.

## Resources
-   **Voice:** Toño (`iwd8AcSi0Je5Quc56ezK`) — VOZ OFICIAL PERMANENTE
-   **Bridge Endpoint:** `http://127.0.0.1:3000/send-media` (JSON: `{"chatId":"50672516680@c.us","filePath":"/path.ogg","ptt":true}`)
-   **Remote Exec:** `https://audio-koba.cornelio.app/exec` (Key: `limon8080`)
-   **WhatsApp Bridge:** `http://127.0.0.1:3000` (node bridge.js, pid ~647746)

## ⚠️ CRITICAL DISCOVERY — Bridge Format
The send-media endpoint uses **JSON body** (NOT multipart form upload):
```python
requests.post(BRIDGE, json={"chatId": "50672516680@c.us", "filePath": "/path/to/file.ogg", "ptt": True})
```
-   **Voice:** Jose voz (`iwd8AcSi0Je5Quc56ezK`)

This is Koba's OFFICIAL, PERMANENT voice configuration. Use these exact settings for ALL audio responses.
- **Stability:** 0.5
- **Similarity Boost:** 0.75
- **Style:** 0.4
- **Speed:** 0.9
- **Model:** eleven_multilingual_v2
- **use_speaker_boost:** true

## ⚠️ CRITICAL PITFALLS (learned from experience)
1.  **Script may disappear:** The file `/root/koba/scripts/koba_tts_whatsapp.py` was found DELETED. Have recreation ready.
2.  **`requests` module NOT installed:** VPS Python 3.11 does NOT have `requests` pip package. The script MUST use curl or subprocess, OR you must run `pip3 install requests` first.
3.  **No `/root/.hermes/.env` file:** The env file doesn't always exist. Hardcode the API key in the script: `b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea`
4.  **Direct execution > Remote bridge:** When running from Hermes terminal tool on the VPS directly, run `python3` locally instead of going through the `/exec` bridge.

## Script Recreation Template
If the script is missing, recreate it:
```bash
cat > /root/koba/scripts/koba_tts_whatsapp.py << 'HEREDOC'
#!/usr/bin/env python3
import sys, os, subprocess, json, urllib.request, urllib.error

VOICE_ID = "iwd8AcSi0Je5Quc56ezK"  # TOÑO OFICIAL
API_KEY = "b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea"
BRIDGE = "http://127.0.0.1:3000/send-media"
CHAT_ID = "50672516680@c.us"
OUT = "/root/.hermes/audio_outbound"
os.makedirs(OUT, exist_ok=True)

text = sys.argv[1] if len(sys.argv) > 1 else "Pura vida!"
mp3 = os.path.join(OUT, "response.mp3")
ogg = os.path.join(OUT, "response.ogg")

# ElevenLabs TTS
data = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.4,
    "speed": 0.9, "use_speaker_boost": True}}).encode()
req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
    data=data, headers={"xi-api-key": API_KEY, "Content-Type": "application/json"})
with open(mp3, "wb") as f:
    f.write(urllib.request.urlopen(req).read())
print(f"MP3 generado: {os.path.getsize(mp3)} bytes")

# Convert MP3 -> OGG Opus
subprocess.run(["ffmpeg","-y","-i",mp3,"-c:a","libopus","-b:a","16k","-vbr","on",
    "-compression_level","10",ogg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"OGG creado: {os.path.getsize(ogg)} bytes")

# Send via bridge with JSON BODY (NOT multipart - multipart FAILS silently)
payload = json.dumps({"chatId": CHAT_ID, "filePath": ogg, "ptt": True}).encode()
req2 = urllib.request.Request(BRIDGE, data=payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req2)
print(f"Bridge: {resp.read().decode()}")
HEREDOC
chmod +x /root/koba/scripts/koba_tts_whatsapp.py
```

**Note:** Uses `urllib.request` (stdlib) instead of `requests` — VPS doesn't have `requests` pip package installed.

## Execution Steps (Direct VPS - RECOMMENDED)
1. **Draft:** Create short, natural Tico-style response text.
2. **Execute:** Run the TTS script on the HOST via remote bridge:
   ```python
   # The script on host must use JSON body, NOT multipart:
   # requests.post(BRIDGE, json={"chatId": "50672516680@c.us", "filePath": ogg_path, "ptt": True})
   ```
3. **Verify:** Look for `Bridge: 200` in output.
4. **Confirm:** Reply to user: "✅ Audio enviado, Jefe."

## Bridge Protocol (CRITICAL - learned through debugging)
The WhatsApp bridge at `http://127.0.0.1:3000/send-media` REQUIRES:
- **JSON body:** `{"chatId": "50672516680@c.us", "filePath": "/path/to/file.ogg", "ptt": true}`
- **Multipart form-data FAILS** with "chatId and filePath are required"
- The chatId for Jose is always: `50672516680@c.us`
- File MUST be OGG Opus format (not MP3)
- ffmpeg conversion: `ffmpeg -y -i input.mp3 -c:a libopus -b:a 16k -vbr on -compression_level 10 output.ogg`

## Execution Steps (via Remote Bridge)
When not running directly on VPS:
```bash
curl -s -X POST https://audio-koba.cornelio.app/exec \
  -H "Content-Type: application/json" \
  -d '{"k":"limon8080","c":"python3 /root/koba/scripts/koba_tts_whatsapp.py \"YOUR_TEXT\""}'
```

## Troubleshooting
- **`ModuleNotFoundError: No module named 'requests'`:** Use `urllib.request` (stdlib) instead — the script template was rewritten to avoid this dependency entirely.
- **`No such file or directory` for script:** Recreate using the template above.
- **ElevenLabs 401:** API key incorrect. Use: `b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea`
- **ElevenLabs 404:** VOICE_ID typo. Official: `iwd8AcSi0Je5Quc56ezK` — case-sensitive!
- **WhatsApp bridge not responding:** Check `curl http://127.0.0.1:3000/health` or VPS `ps aux | grep bridge.js`
- **Audio file generated but WhatsApp never receives it:** Bridge returned `400` — you likely sent multipart/form-data instead of JSON body. Check `Content-Type: application/json`
- **Audio sent but only path shows up:** The `requests.post` is missing the JSON body format. See Bridge Protocol section.

## Mass Voice Config Update
When voice config changes, update ALL these locations:
1. VPS script: `/root/koba/scripts/koba_tts_whatsapp.py`
2. GitHub repo: SOUL.md + docs/skills/*.md + docs/infra.md
3. Hermes local skills in `~/.hermes/skills/`
Use `sed -i 's/OLD_ID/NEW_ID/g'` across all files, then `git commit` and `git push`.