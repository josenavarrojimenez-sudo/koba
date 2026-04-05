# Infraestructura Koba

## VPS Hostinger
- **Host**: srv1443323.hstgr.cloud:22
- **User**: root

## Servicios

### Hermes WhatsApp
- Corre en HOST (root@srv1443323), NO en contenedores
- Audio inbound: `/root/.hermes/audio_cache/*.ogg`
- Audio outbound: `/root/.hermes/audio_outbound/*.ogg`

### ElevenLabs Audio Pipeline
- **STT**: Scribe V1
- **Endpoint**: https://api.elevenlabs.io/v1/speech-to-text
- **Campo archivo**: `file` (NO `audio`)
- **Model ID**: `scribe_v1`
- **TTS Voice ID**: It2gr23I5JuOyLYBui1t

### Kobaco (Paperclip)
- URL: kobaco.cornelio.app:3200
- systemd: kobaco.service
- Source: /root/paperclip
- Company ID: ebe7e870-9b29-4e42-beb0-37973d78e324
- DB: postgresql://paperclip:paperclip123@<docker_ip>:5432/paperclip

### Cloudflare Tunnel
- Tunnel ID: 2a1e9aa4-d556-4c90-a1ce-6a461720eb8e
- Routes: audio-koba.cornelio.app → :9999, kobaco → :3200

### Audio Daemon v5
- Script: /opt/koba_audio_daemon.py
- Service: koba-daemon (systemd, enabled)
- Watch: /root/.hermes/audio_cache/
- Output: /root/.hermes/audio_inbound/
- Bridge HTTP: :9999 (/health, /latest, /transcriptions, /text/{name})
- Log: /var/log/koba_daemon_v5.log
- Health check: /opt/koba_health_check.sh
