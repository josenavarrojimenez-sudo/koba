#!/usr/bin/env python3
import sys, os, subprocess, json, urllib.request, urllib.error

VOICE_ID = "iwd8AcSi0Je5Quc56ezK"  # VOZ OFICIAL TOÑO
API_KEY = "b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea"
BRIDGE = "http://127.0.0.1:3000/send-media"
CHAT_ID = "50672516680@c.us"
OUT = "/root/.hermes/audio_outbound"
os.makedirs(OUT, exist_ok=True)

text = sys.argv[1] if len(sys.argv) > 1 else "Pura vida, Jose!"
mp3 = os.path.join(OUT, "response.mp3")
ogg = os.path.join(OUT, "response.ogg")

# ElevenLabs TTS - CONFIG OFICIAL
data = json.dumps({
    "text": text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.4,
        "speed": 0.9,
        "use_speaker_boost": True
    }
}).encode()
req = urllib.request.Request(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
    data=data,
    headers={"xi-api-key": API_KEY, "Content-Type": "application/json"}
)
try:
    with open(mp3, "wb") as f:
        f.write(urllib.request.urlopen(req).read())
    print(f"MP3 generado: {os.path.getsize(mp3)} bytes")
except urllib.error.HTTPError as e:
    print(f"ElevenLabs error: {e.code} - {e.read().decode()}")
    sys.exit(1)

# Convert MP3 -> OGG Opus
subprocess.run(["ffmpeg","-y","-i",mp3,"-c:a","libopus","-b:a","16k","-vbr","on","-compression_level","10",ogg],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"OGG creado: {os.path.getsize(ogg)} bytes")

# Send via bridge with JSON BODY
payload = json.dumps({"chatId": CHAT_ID, "filePath": ogg, "ptt": True}).encode()
req2 = urllib.request.Request(BRIDGE, data=payload, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req2)
result = resp.read().decode()
print(f"Bridge response: {result}")

