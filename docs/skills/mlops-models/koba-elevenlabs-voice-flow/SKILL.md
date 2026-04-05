---
name: koba-elevenlabs-voice-flow
description: Strategic integration of ElevenLabs API for high-fidelity Tico voice (Toño) and precise transcription (Scribe V2).
tags: [elevenlabs, stt, tts, voice, audio]
---

# ElevenLabs Voice Flow (Koba Custom)

Strategic integration of ElevenLabs API for high-fidelity Tico voice (Toño) and precise transcription (Scribe V2).

## STT Workflow (Scribe V2)
1. Receive `.ogg` (Opus) from WhatsApp/Telegram.
2. Endpoint: `https://api.elevenlabs.io/v1/speech-to-text`
3. Parameters:
   - `model_id`: `scribe_v2`
   - `language_code`: `es`
4. Handle JSON response for `text`.

## TTS Workflow (Toño - Persona Koba)
1. Text input (includes emotional tags like [laughs] or [excited] in the API call but stripped from text logs).
2. Voice ID: `iwd8AcSi0Je5Quc56ezK` (TOÑO OFICIAL)
3. Endpoint: `https://api.elevenlabs.io/v1/text-to-speech/iwd8AcSi0Je5Quc56ezK`
4. Parameters:
   - `model_id`: `eleven_multilingual_v2`
   - `voice_settings`: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.4, "speed": 0.9, "use_speaker_boost": true}`
5. Format Conversion:
   - Output from API: `.mp3`
   - Convert to `.ogg` (Opus) using ffmpeg: `/home/node/ffmpeg -i input.mp3 -c:a libopus output.ogg`
6. Delivery: Send as voice message (`asVoice: true`) using `MEDIA:/path/to/file.ogg`.

## Infrastructure & Troubleshooting (Docker/Hostinger Matrix)
- **The "Media Bridge" Constraint**: When running Koba inside a Docker container while the Messaging Gateway runs on the host (Hostinger VPS), local paths like `/tmp/` are invisible to the gateway.
- **Official Solution**: Map the host's Hermes audio cache directory directly to the container.
  - **YAML Volume**: `- /root/.hermes/audio_cache:/root/.hermes/audio_cache`
- **Binary Stability**: In Hostinger/Docker environments, `/tmp` may have `noexec` flags. Always install/link `ffmpeg` in a persistent, executable path like `/usr/local/bin/ffmpeg`.
- **MIME & Handshake**: For WhatsApp to render a "Circular Voice Note," the file **must** be OGG/Opus and must be placed in the mapped `audio_cache` folder so the host gateway can "hand it off" to the Baileys bridge.
- **Rule 2.5 Enforcement**: If the file doesn't arrive as a playable audio bubble, the "Modal Reciprocity" is broken. Verify volume mapping first.
