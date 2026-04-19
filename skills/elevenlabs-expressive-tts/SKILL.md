---
name: elevenlabs-expressive-tts
description: Add emotional expression tags to text for ElevenLabs TTS v2/v3 - transforms flat text into expressive, emotionally-rich speech with [laughs], [excited], [whispers] tags
category: creative
---

# ElevenLabs Expressive TTS - Emotional Expression Tags

Transform flat text into emotionally expressive speech for ElevenLabs TTS by adding expressive tags and punctuation cues.

## When to Use

Use this skill whenever generating TTS audio with ElevenLabs and the text sounds too flat, robotic, or lacks emotional range. Essential for:
- Voice messages that need personality
- Conversational responses with emotional context
- Storytelling or dramatic content
- Any TTS output where natural human expression matters

## Expressive Tags (ElevenLabs v2/v3)

The model interprets tags in square brackets to change emotional delivery. **Tags affect the next 4-5 words**.

### Available Tags

| Tag | Effect | Use Case |
|-----|--------|----------|
| `[laughs]` | Adds laughter | After jokes, light moments |
| `[chuckles]` | Soft laugh | Amused, gentle humor |
| `[sighs]` | Audible sigh | Relief, exhaustion, contemplation |
| `[whispers]` | Quieter, intimate tone | Secrets, confidential info |
| `[excited]` | Higher energy, enthusiasm | Good news, celebrations |
| `[sad]` | Lower, slower delivery | Bad news, empathy |
| `[surprised]` | Sharp intonation | Unexpected information |
| `[confused]` | Uncertain tone | Questions, hesitation |
| `[angry]` | Stronger, sharper delivery | Frustration, strong opinions |
| `[nervous]` | Hesitant, shaky | Anxiety, uncertainty |
| `[confident]` | Clear, assertive | Important statements, conclusions |
| `[warm]` | Friendly, welcoming | Greetings, positive feedback |
| `[serious]` | Grave, focused | Critical information, warnings |
| `[playful]` | Light, teasing | Banter, casual conversation |
| `[cries]` | Emotional, dramatic | Very sad content (use sparingly) |
| `[gasps]` | Sharp intake of breath | Shock, surprise |
| `[clears throat]` | Preparation sound | Before important statements |
| `[pauses]` | Brief silence | Dramatic effect, transition |

## Text Techniques for Natural Speech

### 1. Punctuation for Pacing

```
Use ellipsis (...) for natural pauses or hesitation
"Déjame pensar... sí, eso tiene sentido"

Use em-dash (—) for interruptions or abrupt changes
"Iba a decirte—espera, mejor te lo muestro"

Use commas for micro-pauses
"Bueno, la verdad, es que sí funciona"

Exclamation for energy (use sparingly)
"¡Esto es increíble!"
```

### 2. Descriptive Context Cues

Add brief narrative cues to guide the model:

```
"¡No puedo creerlo!", dijo con alegría
"Es complicado...", respondió con duda
"Escucha bien:", en tono serio
```

### 3. Capitalization for Emphasis

```
"Esto es MUY importante" (emphasis on MUY)
"NO puedo hacerlo" (strong negation)
```

**Warning:** Don't overuse caps—1-2 words per sentence max.

## ⭐ CONFIGURACIÓN DE ORO - KOBA (AGAS)

**Voice ID:** `pNInz6obpgDQGcFmaJgB`
**Modelo:** `eleven_v3` (ÚNICO que interpreta etiquetas expresivas)

```yaml
elevenlabs:
  voice_id: pNInz6obpgDQGcFmaJgB
  model_id: eleven_v3
  stability: 0.35          # Más variación emocional
  similarity_boost: 0.75   # Fiel a la voz con flexibilidad
  style: 0.65              # Máxima expresividad
  use_speaker_boost: true  # Claridad y presencia
```

## Pipeline Completo Koba TTS

### 1. Script Directo (`koba_tts_directo.py`)

Ubicación: `/root/.hermes/scripts/koba_tts_directo.py`

```bash
python3 /root/.hermes/scripts/koba_tts_directo.py "[warm] Tu texto expresivo aquí"
```

**Características:**
- Llama directamente a API ElevenLabs (bypass gateway)
- Formato: `opus_48000_128` (OGG Opus - nativo Telegram)
- Boost de volumen 2.0x con ffmpeg
- Output: `/root/.hermes/audio_cache/koba_voz_TIMESTAMP.ogg`

### 2. Envío a Telegram

Script: `/root/.hermes/scripts/send_telegram_voice.py`

```bash
python3 /root/.hermes/scripts/send_telegram_voice.py 7666543493 /root/.hermes/audio_cache/koba_voz_TIMESTAMP.ogg "Caption opcional"
```

### 3. Flujo Completo en un Comando

```bash
TEXTO="[warm] ¡Perfecto, Jefe! [confident] Todo listo."
python3 /root/.hermes/scripts/koba_tts_directo.py "$TEXTO"
AUDIO=$(ls -t /root/.hermes/audio_cache/koba_voz_*.ogg | head -1)
python3 /root/.hermes/scripts/send_telegram_voice.py 7666543493 "$AUDIO" "🎙️ Koba TTS"
```

## ⚠️ CRITICAL: Model Requirement

**Expressive tags ONLY work with `eleven_v3` model.**

If you use `eleven_multilingual_v2` or other models, the brackets will be **read literally** (you'll hear "[warm] Hola" spoken aloud). This is a common pitfall!

```yaml
# ✅ CORRECT - Tags will work
model_id: eleven_v3

# ❌ WRONG - Tags will be spoken as text
model_id: eleven_multilingual_v2
```

**Why:** The expressive tags feature is exclusive to the v3 model architecture. Earlier models don't parse bracket tags.

## Workflow

### Step 1: Analyze Emotional Context

Read the text and identify:
- Primary emotion (joy, sadness, excitement, concern, etc.)
- Key moments that need emphasis
- Natural pause points
- Places where human speech would have non-verbal cues

### Step 2: Insert Tags Strategically

**Rules:**
- Place tags **before** the words they affect
- Tags influence ~4-5 words ahead
- Don't stack multiple tags (pick one)
- Use 1-3 tags per paragraph max (natural speech isn't constantly labeled)

**Example Transformation:**

Original:
```
Hola Jose, buenos días. Terminé el reporte que me pediste.
Hay algunos puntos importantes que debes revisar.
```

Enhanced:
```
[warm] Hola Jose, buenos días. [confident] Terminé el reporte que me pediste.
[serious] Hay algunos puntos importantes que debes revisar.
```

### Step 3: Add Punctuation Cues

```
Original:
"Bueno la verdad es que no estoy seguro pero creo que funciona"

Enhanced:
[nervous] Bueno... la verdad es que no estoy seguro, pero [confident] creo que funciona.
```

### Step 4: Review for Natural Flow

Read the enhanced text aloud. If it feels over-tagged or unnatural, remove some tags. **Less is often more**.

## Spanish-Specific Considerations

Spanish has different rhythm and emphasis patterns:

```
Use inverted punctuation for questions/exclamations:
[excited] ¡Qué bueno que funciona!

Spanish ellipsis uses three dots with space before:
[sighs] No sé... déjame pensarlo

Common Spanish emotional phrases:
[warm] Hola, ¿cómo estás?
[excited] ¡Esto es increíble!
[sad] Qué pena escuchar eso
[serious] Escucha bien esto
```

## Examples

### Casual Conversation
```
Original:
"Hey, ¿viste el mensaje? Respondí lo que preguntaste."

Enhanced:
[warm] Hey, ¿viste el mensaje? [confident] Respondí lo que preguntaste.
```

### Exciting News
```
Original:
"Funcionó el deployment. Todos los tests pasan."

Enhanced:
[excited] ¡Funcionó el deployment! [chuckles] Todos los tests pasan.
```

### Serious Update
```
Original:
"Necesito que revises esto. Hay un error crítico."

Enhanced:
[serious] Necesito que revises esto. [pauses] Hay un error crítico.
```

### Empathetic Response
```
Original:
"Entiendo que es frustrante. Vamos a solucionarlo."

Enhanced:
[warm] Entiendo que es frustrante... [confident] Vamos a solucionarlo.
```

### Storytelling
```
Original:
"Entonces entró al cuarto y no podía creer lo que vio."

Enhanced:
[whispers] Entonces entró al cuarto... [gasps] y no podía creer lo que vio.
```

## Common Pitfalls

❌ **Over-tagging:**
```
[excited] Hola [warm] Jose [confident] ¿cómo [playful] estás?
```
→ Feels robotic and unnatural

✅ **Natural tagging:**
```
[warm] Hola Jose, ¿cómo estás?
```

❌ **Tag too far from target:**
```
[excited] Esto es algo que quiero decirte desde hace mucho tiempo y es importante
```
→ Tag only affects first 4-5 words

✅ **Tag close to target:**
```
Quiero decirte algo... [excited] ¡es increíble!
```

❌ **Conflicting emotions:**
```
[sad] ¡Esto es fantástico!
```
→ Mixed signals confuse the model

## Integration with text_to_speech Tool

Before calling `text_to_speech`, process the text through this skill:

```python
# Example pattern
original_text = "Hola, terminé el trabajo"
enhanced_text = add_expressive_tags(original_text, context="positive completion")
text_to_speech(text=enhanced_text)
```

## Verification

After generating audio:
1. Listen for natural emotional flow
2. Check if tags produced intended effect
3. Adjust tag placement or intensity if needed
4. Note which tags work best with your voice ID

## Related

- Direct ElevenLabs integration in Hermes TTS pipeline
- Voice ID selection for emotional range
- Punctuation patterns for speech synthesis
