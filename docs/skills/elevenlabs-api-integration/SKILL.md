---
name: elevenlabs-api-integration
description: Strategic integration of ElevenLabs API for high-fidelity TTS (Toño voice) and STT (Scribe V2) with Tico accent support, including OGG/Opus conversion for WhatsApp/Telegram.
version: 1.0.0
author: Koba
---

# ElevenLabs API Strategic Integration

Customized integration for Jose Navarro's environment (Hermes), focusing on the 'Toño' voice and Scribe V2 for Costa Rican accent recognition.

## Core Components

### 1. TTS with Toño Voice (eleven_v3)
Uses the `v1/text-to-speech/{voice_id}` endpoint.

**Config:**
- **Voice ID**: `It2gr23I5JuOyLYBui1t`
- **Model**: `eleven_v3`
- **Settings**: Stability 0.5, Similarity Boost 0.8, Speaker Boost enabled.

### 2. STT with Scribe V2
Uses the `v1/speech-to-text` endpoint with `multipart/form-data`. Specifically chosen for robustness with Costa Rican regionalisms.

### 3. Media Conversion (OGG/Opus)
Mandatory for native voice bubbles on WhatsApp/Telegram.
```bash
ffmpeg -i input.mp3 -c:a libopus -track_mapping 0 -application voip output.ogg -y
```

## Implementation Script (Bash/Curl)

```bash
#!/bin/bash
# tts_toño.sh
TEXT=$1
OUTPUT=${2:-/tmp/koba_voice.ogg}
API_KEY="REDACTED"
VOICE_ID="It2gr23I5JuOyLYBui1t"

curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE_ID" \
     -H "Accept: audio/mpeg" \
     -H "Content-Type: application/json" \
     -H "xi-api-key: $API_KEY" \
     -d "{
       \"text\": \"$TEXT\",
       \"model_id\": \"eleven_v3\",
       \"voice_settings\": {
         \"stability\": 0.5,
         \"similarity_boost\": 0.8,
         \"style\": 0.0,
         \"use_speaker_boost\": true
       }
     }" -o /tmp/temp_audio.mp3

ffmpeg -i /tmp/temp_audio.mp3 -c:a libopus -application voip "$OUTPUT" -y
rm /tmp/temp_audio.mp3
```

## Pitfalls & Lessons
- **Model Selection**: Always use `eleven_v3` for the most natural emotional range.
- **Conversion**: Raw MP3s sent to Telegram/WhatsApp appear as files, not voice bubbles. `libopus` with `voip` application is required.
- **Header Auth**: ElevenLabs uses `xi-api-key` header, not standard `Bearer` tokens.
