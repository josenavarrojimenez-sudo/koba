#!/usr/bin/env python3
import requests, subprocess, sys, os, uuid

API = "b2ecfb5a8783c04b35e22208f6df9a423c86878866349e686fc044e49c8e7bea"
VOICE = "iwd8AcSi0Je5Quc56ezK"
BRIDGE = "http://127.0.0.1:3000/send-media"
TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}"

def send_audio(text, desc=""):
    try:
        ogg = f"/tmp/koba_{uuid.uuid4().hex[:8]}.ogg"
        r = requests.post(TTS_URL,
            headers={"xi-api-key": API, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                                    "style": 0.6, "use_speaker_boost": True}},
            timeout=30)
        print(f"[{desc}] TTS status: {r.status_code}")
        if r.status_code != 200:
            print(f"[{desc}] ERROR: {r.text[:200]}")
            return
        mp3 = ogg.replace(".ogg", ".mp3")
        with open(mp3, "wb") as f: f.write(r.content)
        size_mb = os.path.getsize(mp3) / 1048576
        print(f"[{desc}] MP3 size: {size_mb:.1f} MB")
        sub = subprocess.run(["ffmpeg", "-y", "-i", mp3, "-c:a", "libopus", "-b:a", "16k",
                        "-vbr", "on", "-compression_level", "10", ogg],
                       capture_output=True, timeout=10)
        print(f"[{desc}] FFMPEG rc={sub.returncode}")
        if sub.returncode != 0:
            print(f"[{desc}] FFmpeg err: {sub.stderr.decode()[:200]}")
            return
        with open(ogg, "rb") as f:
            resp = requests.post(BRIDGE,
                files={"file": ("answer.ogg", f, "audio/ogg")},
                data={"ptt": "true"}, timeout=15)
        print(f"[{desc}] Bridge: {resp.status_code} {resp.text[:150]}")
        os.remove(mp3); os.remove(ogg)
    except Exception as e:
        print(f"[{desc}] ERROR: {e}")

send_audio("Jajaja, ¡no Jefe! ¡Me estoy muriendo de la risa! ¡Jajaja, qué buena onda! ¡Pura vida, hermano!", "RISA")
send_audio("Shhh... Jefe, estoy susurrando muy bajito... (susurrando más quedo) pura vida en secreto...", "SUSURRO")
send_audio("Ay Jefe... la verdad estoy muy triste ahorita... todo se siente gris y pesado... no sé si puedo con esto, loco...", "TRISTE")
