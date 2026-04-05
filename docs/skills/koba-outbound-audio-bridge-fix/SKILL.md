---
name: koba-outbound-audio-bridge-fix
category: koba-infra
description: Workaround for sending audio responses to Jose via WhatsApp when Hermes `text_to_speech` tool fails to deliver the file natively. Involves generating OGG Opus on the host and sending via OpenClaw/Hermes commands.
---

# Koba Outbound Audio Bridge Fix

## Problem
When using the `text_to_speech` tool in Hermes, the audio file is generated inside the Koba sandbox but the WhatsApp gateway (running on the VPS or a different container) cannot access it to send it to the user. The user receives the text response but not the audio file.

## Solution
Generate the audio file **directly on the VPS host** in a shared location, then trigger the WhatsApp gateway to send it.

### Prerequisities
*   SSH access to the VPS Host (e.g., via `paramiko` from Koba's terminal).
*   ElevenLabs API Key.
*   Voice ID (Toño): `iwd8AcSi0Je5Quc56ezK`.

### Steps

1.  **Generate Audio on Host via API:**
    Run a curl command on the host to generate Opus audio compatible with WhatsApp (output_format=opus_48000_64).
    ```bash
    curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=opus_48000_64" \
      -H "xi-api-key: {ELEVEN_API_KEY}" \
      -H "Content-Type: application/json" \
      -d '{"text": "Your response text here"}' \
      -o /tmp/koba_response.ogg
    ```

2.  **Send via Gateway:**
    Use the active WhatsApp bridge to send the file.
    *   **If using OpenClaw:**
        ```bash
        docker exec openclaw-container openclaw message send --channel whatsapp --to +{USER_PHONE} --media /tmp/koba_response.ogg
        ```
    *   **If using Hermes Baileys:**
        Locate the hermes command or script inside the Hermes container that sends media.
        Typically: `hermes message send ...` or via the `send_message` tool if the file is accessible to the bridge.

## Critical Notes
*   **Format:** WhatsApp *requires* OGG Opus. The `opus_48000_64` format in the ElevenLabs API works perfectly. Do not send MP3 directly without transcoding if possible, though some bridges handle MP3.
*   **Permissions:** The container running the WhatsApp sender must have read access to `/tmp/koba_response.ogg` or the file must be copied inside a volume map.