---
name: elevenlabs-telegram-voice-pipeline
description: Complete pipeline for sending expressive ElevenLabs TTS audio to Telegram as voice notes — direct API bypass with ffmpeg boost and sendVoice
category: creative
---

# ElevenLabs → Telegram Voice Pipeline

Complete end-to-end workflow for generating expressive TTS audio with ElevenLabs and sending it as a native voice note to Telegram.

## When to Use

Use this pipeline when:
- You need **expressive, emotional voice** (not flat/robotic)
- Sending voice messages via **Telegram bot**
- Built-in `text_to_speech` tool doesn't work (format issues, etc.)
- You need **volume boost** for mobile playback clarity
- Want **direct API control** over voice parameters

## ⚠️ Why Not Use Built-in TTS Tool?

The Hermes `text_to_speech` tool has limitations:
- May not support `eleven_v3` model (no bracket tags)
- No volume boost for mobile devices
- Less control over output format
- Gateway routing can fail

**This pipeline bypasses the gateway** and calls ElevenLabs + Telegram APIs directly.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Text with      │────▶│  ElevenLabs API  │────▶│  OGG Audio File │
│  [expressive]   │     │  (eleven_v3)     │     │  (opus_48000)   │
│  tags           │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram User  │◀────│  Telegram Bot    │◀────│  ffmpeg Boost   │
│  (Voice Note)   │     │  sendVoice API   │     │  (volume=2.0)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Prerequisites

1. **API credentials configured** in environment or `.env` file
2. **ffmpeg installed**: `which ffmpeg` should return `/usr/bin/ffmpeg`
3. **Python libraries**: `pip install requests python-telegram-bot`

## Scripts

### 1. TTS Generator: `koba_tts_directo.py`

Location: `/root/.hermes/scripts/koba_tts_directo.py`

**Features:**
- Calls ElevenLabs Text-to-Speech API directly
- Uses `eleven_v3` model (supports expressive tags)
- Applies 2.0x volume boost with ffmpeg
- Outputs OGG Opus format (native Telegram)

**Usage:**
```bash
python3 /root/.hermes/scripts/koba_tts_directo.py "[warm] Tu texto expresivo aquí"
```

**Output:** `/root/.hermes/audio_cache/koba_voz_TIMESTAMP.ogg`

### 2. Telegram Sender: `send_telegram_voice.py`

Location: `/root/.hermes/scripts/send_telegram_voice.py`

**Features:**
- Reads bot token from environment or `.env`
- Sends audio as native voice note (not audio file)
- Supports optional caption

**Usage:**
```bash
python3 /root/.hermes/scripts/send_telegram_voice.py <chat_id> <audio_path> [caption]
```

**Example:**
```bash
python3 /root/.hermes/scripts/send_telegram_voice.py 7666543493 /root/.hermes/audio_cache/koba_voz_20260419_065921.ogg "🎙️ Mensaje de Koba"
```

## Complete Workflow

### Step 1: Generate Audio with Expressive Tags

```bash
TEXT="[warm] ¡Hola Jose! [confident] Todo listo para la reunión."
python3 /root/.hermes/scripts/koba_tts_directo.py "$TEXT"
```

### Step 2: Send to Telegram

```bash
AUDIO=$(ls -t /root/.hermes/audio_cache/koba_voz_*.ogg | head -1)
python3 /root/.hermes/scripts/send_telegram_voice.py 7666543493 "$AUDIO" "🎙️ Koba"
```

### Step 3: One-Liner Pipeline

Create `send_koba_voice.sh`:
```bash
#!/bin/bash
TEXT="$1"
CHAT_ID="${2:-7666543493}"

python3 /root/.hermes/scripts/koba_tts_directo.py "$TEXT"
AUDIO=$(ls -t /root/.hermes/audio_cache/koba_voz_*.ogg | head -1)
python3 /root/.hermes/scripts/send_telegram_voice.py "$CHAT_ID" "$AUDIO" "🎙️ Koba"
```

Usage:
```bash
./send_koba_voice.sh "[excited] ¡Buenas noticias! El proyecto está listo."
```

## Expressive Tags Reference

Tags that work with `eleven_v3` (affect next 4-5 words):

| Tag | Effect | Example |
|-----|--------|---------|
| `[warm]` | Friendly, welcoming | `[warm] Hola, ¿cómo estás?` |
| `[confident]` | Assertive, sure | `[confident] Esto va a funcionar.` |
| `[excited]` | High energy | `[excited] ¡Esto es increíble!` |
| `[serious]` | Grave, focused | `[serious] Necesito tu atención.` |
| `[chuckles]` | Light laugh | `[chuckles] Bueno, sí...` |
| `[sighs]` | Audible sigh | `[sighs] Es complicado...` |
| `[whispers]` | Quiet, intimate | `[whispers] Te cuento un secreto...` |
| `[surprised]` | Sharp intonation | `[surprised] ¿En serio?` |
| `[sad]` | Lower, slower | `[sad] Qué pena escuchar eso.` |

**Important:** Tags are **NOT spoken** — they modify delivery. Don't use in normal text responses, only for TTS input.

## Configuration

### Voice Settings (in koba_tts_directo.py)

```python
VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Koba's voice
MODEL_ID = "eleven_v3"            # Required for [tags]

VOICE_SETTINGS = {
    "stability": 0.35,            # Lower = more variation
    "similarity_boost": 0.75,     # Keep voice identity
    "style": 0.65,                # Higher = more expressive
    "use_speaker_boost": True
}
```

### Output Format

```python
OUTPUT_FORMAT = "opus_48000_128"  # OGG Opus - native Telegram
```

### Volume Boost

```bash
ffmpeg -i input.ogg -filter:a 'volume=2.0' -c:a libopus -b:a 128k output.ogg
```

**Why 2.0x boost?** Mobile speakers are quiet — boost ensures clarity.

## Troubleshooting

### Problem: Audio sounds flat/robotic

**Solution:** Ensure you're using `eleven_v3` model, not `eleven_multilingual_v2`:

```python
MODEL_ID = "eleven_v3"  # ✅ Correct
# MODEL_ID = "eleven_multilingual_v2"  # ❌ No tag support
```

### Problem: Tags are spoken aloud

**Cause:** Wrong model — `eleven_multilingual_v2` reads tags as text.

**Solution:** Switch to `eleven_v3`.

### Problem: Telegram says "Unauthorized"

**Cause:** Invalid bot token in environment.

**Solution:** Verify token is set correctly in environment or `.env` file.

### Problem: Audio file too quiet

**Solution:** Increase ffmpeg boost:
```bash
ffmpeg -i input.ogg -filter:a 'volume=3.0' ...  # 3x instead of 2x
```

## Related Skills

- `elevenlabs-expressive-tts` — Tag reference and emotional delivery guide
- `web-content-extractor` — Extract content from protected web pages

## Performance

- **TTS Generation:** ~3-8 seconds (depends on text length)
- **ffmpeg Boost:** ~1-2 seconds
- **Telegram Send:** ~1-3 seconds (depends on file size/network)
- **Total:** ~5-13 seconds end-to-end

## Key Files

| File | Purpose |
|------|---------|
| `/root/.hermes/scripts/koba_tts_directo.py` | Generate TTS audio |
| `/root/.hermes/scripts/send_telegram_voice.py` | Send to Telegram |
| `/root/.hermes/audio_cache/` | Output directory |

---

*Created: April 2026*
*Tested with ElevenLabs v3 + Telegram Bot API*
