---
name: youtube-transcript-on-cloud
description: Extract YouTube transcripts when running from cloud VPS infrastructure. YouTube blocks all cloud IPs, requiring workarounds.
category: media
---

# YouTube Transcript Extraction from Cloud VPS

## Problem
YouTube blocks ALL requests from cloud provider IPs (Hostinger, AWS, GCP, Azure, etc.).
Every method returns "Sign in to confirm you're not a bot" or IP blocked errors.

**Confirmed blocked methods:**
- youtube-transcript-api (youtube_transcript_api)
- yt-dlp (all player clients: web, android, tv, ios, embedded)
- ytdlp with --extractor-args youtube:player_client=*
- YouTube innertube API direct calls
- Invidious public instances (down or also blocked)
- Tactiq.io (requires App Check token)
- Direct curl to youtube.com/watch with cookies (LOGIN_REQUIRED)
- youtubetranscript.com and DownSub (also blocks cloud IPs)
- YouTube timedtext API (empty response from cloud IPs)
- DuckDuckGo/Google searches don't help (no transcript mirrors in search results)

## Solution Options (in order of preference)

### Option 1: User Provides Transcript (Fastest)
Ask the user to:
1. Open the video on YouTube
2. Click "..." → "Show transcript"
3. Copy and paste the transcript to you
4. You process it (chapters, summary, blog post, etc.)

### Option 2: User Exports YouTube Cookies (Semi-Permanent)
The user exports cookies from their browser where they're logged into YouTube:
```bash
# Using yt-dlp on their LOCAL machine with an extension like "Get cookies.txt LOCALLY"
# or using browser extension to export cookies as Netscape format
```

Then place on VPS at `/root/yt_cookies.txt` and use:
```bash
yt-dlp --cookies /root/yt_cookies.txt --write-auto-sub \
  --skip-download --sub-lang es,en --sub-format vtt \
  -o "/tmp/%(id)s" "https://youtube.com/watch?v=VIDEO_ID"
```
**Caveat:** Cookies expire after ~2 weeks. YouTube eventually bans the account if used repeatedly from cloud.

### Option 3: Download Audio Locally, Transcribe on VPS
User downloads the audio locally, uploads to VPS, transcribe with ElevenLabs Scribe:
```bash
# On VPS with ElevenLabs Scribe:
curl -X POST "https://api.elevenlabs.io/v1/speech-to-text/scribe_v1" \
  -H "xi-api-key: $ELEVEN_API_KEY" \
  -F "file=@/path/to/audio.mp3" \
  -F "model_id=scribe_v1" \
  -F "language_code=es"
```

### Option 4: Use yt-dlp on Local Machine
User runs `yt-dlp` locally (non-cloud IP) and sends the transcript/text to you.

## When to Use This Skill
- User shares a YouTube video URL for transcript/summary
- You're running on a cloud VPS (Hostinger, etc.)
- No YouTube transcripts are accessible via API

## Quick Resolution Script
When user sends a YouTube link, immediately check if you can extract:
1. Try youtube-transcript-api (will likely fail on cloud)
2. If fails, immediately inform user it's an IP block issue
3. Give them the 4 options above, recommending Option 1 (fastest)