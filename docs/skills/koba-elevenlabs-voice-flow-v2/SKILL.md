---
name: koba-elevenlabs-voice-flow
description: Strategic integration of ElevenLabs API for high-fidelity voice-to-voice interaction (Rule 2.5).
---

# Koba ElevenLabs Voice Flow

Strategic integration of ElevenLabs API for high-fidelity voice-to-voice interaction (Rule 2.5).

## Implementation Details

### Transcription (STT)
- **Model**: Scribe V2 (Mandatory for Tico accent detection).
- **Service**: ElevenLabs API.
- **Script (Host)**: `/root/koba_bridge.sh`
- **Logic**: Reads latest `.ogg` from `/root/.hermes/audio_cache/`, sends to ElevenLabs, returns JSON.

### Voice Generation (TTS)
- **Voice**: Toño (Voice ID: `It2gr23I5JuOyLYBui1t`).
- **Model**: `eleven_v3`.
- **Format**: OGG/Opus (via ffmpeg or direct API request).
- **Script (Docker)**: `/opt/koba_brain/scripts/tts.sh` (CLI mode via curl).

## Pitfalls
- **Docker Isolation**: Host and Agent containers might not share the same `/tmp` or `/data` volumes. Always check mounts via `docker inspect`.
- **Visibility**: Even if the file exists on the host, the Chat Client (WhatsApp/Telegram) inside its own container might not "see" the generated audio file to send it.
