# Audio Pipeline Fix (Success Path)

## Problem
Hermes local transcription failed (`whisper-1` model size error).
Audio files arrive at `/root/.hermes/audio_cache/` but were not being processed.

## Solution: Koba Daemon v7
We wrote a custom Python daemon (`/opt/koba_audio_daemon.py`) that runs on the Host VPS, watches the audio cache folder, and sends files directly to ElevenLabs API.

### Critical Technical Details (Hard Won)
1.  **API Endpoint**: `https://api.elevenlabs.io/v1/speech-to-text`
2.  **Model ID**: Must use `scribe_v1`. (`scribe_v2` failed previously).
3.  **Form Field Name**: Must use `file`.
    *   *Wrong:* `files={'audio': ...}` -> Error 400
    *   *Correct:* `files={'file': ...}` -> Success 200
4.  **Audio Format**: Direct OGG file from WhatsApp works. No `ffmpeg` conversion needed.
5.  **Watch Directory**: `/root/.hermes/audio_cache/`

### Setup Instructions
1.  **Install Dependencies**: `pip3 install requests --break-system-packages`
2.  **Start Daemon**: `nohup python3 -u /opt/koba_audio_daemon.py > /var/log/koba_daemon_v7.log 2>&1 &`
3.  **Verify**: `curl -s http://localhost:9999/latest` (Should return JSON with transcription text).

### Troubleshooting
-   If the daemon crashes or isn't found: Check `ps aux | grep koba`.
-   If audio isn't transcribed: Check if it landed in `/root/.hermes/audio_cache/` (sometimes paths change between `audio_cache` and `cache/audio` - current working path is `/root/.hermes/audio_cache/`).
-   **Bridge Access**: Available via Cloudflare tunnel at `https://audio-koba.cornelio.app/latest`.

### Current Working Script
See `scripts/daemon_v7.py` in this repo.
