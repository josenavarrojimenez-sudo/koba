# Infraestructura de Koba

## VPS Hostinger
- **Host**: `srv1443323.hstgr.cloud:22`
- **User**: `root`

## Servicios

### 1. Hermes WhatsApp
- **Ejecucion**: `hermes whatsapp` corre en HOST (root@srv1443323), NO en contenedores
- **Audio inbound**: `/root/.hermes/audio_cache/*.ogg`
- **Audio outbound**: `/root/.hermes/audio_outbound/*.ogg`

### 2. ElevenLabs Audio Pipeline
- **STT**: ElevenLabs Scribe V1
- **TTS Voice ID**: `iwd8AcSi0Je5Quc56ezK`
- **API Endpoint**: `https://api.elevenlabs.io/v1/speech-to-text`
- **Campo de audio**: `file` (IMPORTANTE - no `audio`)
- **Model ID**: `scribe_v1`

### 3. Kobaco (Paperclip)
- **URL**: `https://kobaco.cornelio.app`
- **Puerto**: 3200 (mapeado a 3100)
- **Source**: `/root/paperclip`
- **Company ID**: `ebe7e870-9b29-4e42-beb0-37973d78e324`
- **CEO(Koba)**: `aef9e8b8-f8ee-42f1-b4b2-760136decec1`
- **Apolo (VP Presupuestos)**: `b0e6f439-4a67-41da-8103-70337f58a9f6`
- **DB**: postgres en docker
  - User: `paperclip`
  - Pass: `paperclip123`
  - DB: `paperclip`

### 4. Cloudflare Tunnel
- **Tunnel ID**: `2a1e9aa4-d556-4c90-a1ce-6a461720eb8e`
- **Rutas**:
  - `audio-koba.cornelio.app` -> `localhost:9999`
  - `kobaco` -> `localhost:3200`

### 5. Audio Daemon (STT)
- **Script**: `/opt/koba_audio_daemon.py`
- **Service**: `koba-daemon` (systemd, enabled en boot)
- **Watch dir**: `/root/.hermes/audio_cache/`
- **Output dir**: `/root/.hermes/audio_inbound/`
- **Bridge HTTP**: puerto 9999
  - `/health` -> health check
  - `/transcriptions` -> todas las transcripciones
  - `/latest` -> ultima transcripcion
  - `/text/{filename}` -> transcripcion especifica
- **Log**: `/var/log/koba_daemon_v5.log`

### 6. Scripts de Mantenimiento
- **Health check**: `/opt/koba_health_check.sh`
