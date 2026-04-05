#!/usr/bin/env python3
"""
Koba Text-to-Voice WhatsApp Pipeline v1
Texto -> ElevenLabs (Toño) -> OGG Opus -> WhatsApp como nota de voz
"""
import subprocess
import requests
import json
import sys
import os
import time
from pathlib import Path

# ============================================================
# CONFIGURACION
# ============================================================
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not ELEVENLABS_API_KEY:
    try:
        with open("/root/.hermes/.env") as f:
            for line in f:
                if line.startswith("ELEVENLABS_API_KEY="):
                    ELEVENLABS_API_KEY = line.split("=", 1)[1].strip()
                    break
    except:
        pass

VOICE_ID = "iwd8AcSi0Je5Quc56ezK"  # Toño
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_DIR = "/root/.hermes/audio_outbound"
WHATSAPP_BRIDGE = "http://127.0.0.1:3000"
FFMPEG = "/usr/bin/ffmpeg"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# FUNCTIONS
# ============================================================
def text_to_mp3(text, voice_id=VOICE_ID):
    """Envíar texto a ElevenLabs y recibir MP3"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    if resp.status_code != 200:
        raise Exception(f"ElevenLabs error {resp.status_code}: {resp.text[:200]}")
    return resp.content

def mp3_to_ogg_opus(mp3_bytes, output_path):
    """Convertir MP3 a OGG Opus con ffmpeg (formato nativo de WhatsApp)"""
    mp3_path = output_path.replace(".ogg", ".mp3")
    with open(mp3_path, "wb") as f:
        f.write(mp3_bytes)
    
    result = subprocess.run([
        FFMPEG,
        "-y",
        "-i", mp3_path,
        "-c:a", "libopus",
        "-b:a", "128k",
        "-vbr", "on",
        "-frame_duration", "60",
        "-application", "voip",
        "-ar", "48000",
        "-ac", "1",
        output_path
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        raise Exception(f"ffmpeg error: {result.stderr[:200]}")
    
    # Clean up mp3
    os.remove(mp3_path)
    return output_path

def send_whatsapp_voice(chat_id, ogg_path, caption=""):
    """Enviar nota de voz por WhatsApp bridge"""
    url = f"{WHATSAPP_BRIDGE}/send-media"
    data = {
        "chatId": chat_id,
        "filePath": ogg_path,
        "mediaType": "audio",
        "caption": caption
    }
    resp = requests.post(url, json=data, timeout=30)
    return resp.json()

def send_voice_text(text, chat_id="50672516680@s.whatsapp.net"):
    """Pipeline completo: texto -> ElevenLabs -> OGG -> WhatsApp"""
    print(f"🎙️ Generando voz de Toño...")
    mp3_bytes = text_to_mp3(text)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    ogg_path = os.path.join(OUTPUT_DIR, f"koba_{timestamp}.ogg")
    
    print(f"🔄 Convirtiendo a OGG Opus...")
    mp3_to_ogg_opus(mp3_bytes, ogg_path)
    
    print(f"📲 Enviando nota de voz...")
    result = send_whatsapp_voice(chat_id, ogg_path)
    
    file_size = os.path.getsize(ogg_path)
    print(f"✅ Enviado! ({file_size} bytes) -> {ogg_path}")
    print(f"   Resultado: {json.dumps(result, indent=2)}")
    
    return ogg_path, result

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: koba_tts.py 'texto a convertir' [chat_id]")
        print("Ejemplo: koba_tts.py 'Hola Jefe, todo listo' 50672516680@s.whatsapp.net")
        sys.exit(1)
    
    text = sys.argv[1]
    chat_id = sys.argv[2] if len(sys.argv) > 2 else "50672516680@s.whatsapp.net"
    
    if not ELEVENLABS_API_KEY:
        print("❌ Error: ELEVENLABS_API_KEY no configurada")
        sys.exit(1)
    
    try:
        path, result = send_voice_text(text, chat_id)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)