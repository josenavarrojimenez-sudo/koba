---
name: youtube-transcript-cloud-workaround
description: Extract YouTube transcripts when running from cloud VPS infrastructure where YouTube blocks all direct requests. Multiple fallback approaches.
category: media
---

# YouTube Transcript Extraction - Cloud VPS Workarounds

## Problem
YouTube COMPLETELY blocks cloud provider IPs (Hostinger VPS, AWS, GCP, Azure). This affects:
- `youtube-transcript-api` → RequestBlocked/IPBlocked
- `yt-dlp` → "Sign in to confirm you're not a bot"
- All YouTube API endpoints → LOGIN_REQUIRED
- Direct page scraping → consent redirects

## What DOESN'T Work (all tested and failed)
1. ❌ `youtube-transcript-api` fetch() — blocked by YouTube
2. ❌ `yt-dlp` with `--write-auto-sub` — bot detection
3. ❌ `yt-dlp` with `player_client=android` — LOGIN_REQUIRED
4. ❌ `yt-dlp` with `player_client=tv` — LOGIN_REQUIRED
5. ❌ `yt-dlp` with `player_client=web` — bot detection
6. ❌ `youtubetranscript.com` API — 502 Bad Gateway
7. ❌ Invidious instances (vid.puffyan.us, invidious.lunar.icu) — dead or 404s
8.  innertube API (`/youtubei/v1/get_transcript`) — FAILED_PRECONDITION
9. ❌ Direct page fetch with CONSENT cookie — consent redirect loop

## What MIGHT Work (untested or edge cases)
1. **Cookie-based yt-dlp**: Export cookies from local browser (`--cookies-from-browser chrome` or `--cookies cookies.txt`). Works for ~2 weeks until account gets flagged.
2. **Proxy**: Route through residential proxy to hide cloud IP.
3. **Browser tool**: If Playwright/Chrome is installed (not available on minimal VPS).

## Recommended Workarounds

### Option A: Audio Transcription via ElevenLabs (RELIABLE)
1. Download audio with yt-dlp (sometimes works for audio-only):
```bash
yt-dlp -x --audio-format mp3 -o /tmp/yt_audio.mp3 VIDEO_URL
```
2. Transcribe with ElevenLabs Scribe:
```python
import requests
with open("/tmp/yt_audio.mp3", "rb") as f:
    resp = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text/scribe_v1",
        headers={"xi-api-key": API_KEY},
        files={"file": ("yt_audio.mp3", f, "audio/mpeg")},
        data={"model_id": "scribe_v1", "language_code": "es"}
    )
    text = resp.json()["text"]
```

### Option B: Manual Copy
Ask user to paste transcript from YouTube's built-in subtitle panel (click "..." → "Show transcript").

### Option C: Web Search
Search for existing transcriptions/summaries of the video on blogs or recap sites.

## Pitfalls
1. YouTube's IP blocks are IP-range based — even different cloud providers get blocked
2. Even with cookies, account can get permanently banned
3. yt-dlp needs JavaScript runtime (deno) for some operations
4. PDF conversion to images works (pdftoppm) — but that's for Vision AI, not YouTube

## Cost
- ElevenLabs Scribe: ~$0.36/hour of audio
- Alternative: Free Gemini 2.5 Flash Thinking for summarizing copied text
