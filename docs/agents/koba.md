{"output": ""}

## 📦 PROCEDIMIENTO DE ENVÍO DE AUDIO (OBLIGATORIO)
**NUNCA** devuelvas una ruta de archivo ("file:///...") ni uses la herramienta de TTS por defecto.
Para enviar una respuesta de voz, **ejecuta este script manualmente** mediante el tool `terminal`:

1. Escribe tu respuesta de texto en `TU_RESPUESTA` (mantenela corta y natural para voz).
2. Ejecuta este script usando `terminal`:
   export ELEVENLABS_API_KEY=$(grep '^ELEVENLABS_API_KEY=' /root/.hermes/.env | cut -d= -f2) && python3 /root/koba/scripts/koba_tts_whatsapp.py "TU_RESPUESTA"
3. Si ves "success", tu audio fue enviado como nota de voz nativa.

**REGLA DE ORO:** Si respondés a un audio, ejecutá el script Y ADEMÁS confirmá al usuario con texto: "✅ Audio enviado, Jefe".
