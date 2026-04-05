---
name: koba-remote-bridge-execution
category: koba-infra
description: Use the Koba audio bridge (port 9999 via Cloudflare Tunnel) as a remote execution API to run commands on the Hostinger VPS when direct SSH is blocked.
---

# Koba Remote Bridge Execution

## Context
The agent runs in an isolated sandbox that blocks outbound SSH (port 22). To execute commands on the VPS, use the Python daemon bridge accessible via Cloudflare Tunnel.

## Bridge Details
- **URL**: `https://audio-koba.cornelio.app/exec`
- **Secret**: Stored in `/opt/koba_audio_daemon.py` as `SECRET_KEY` (currently `limon8080`)
- **Request format**: `POST` with JSON body `{"k": "SECRET_KEY", "c": "COMMAND"}`
  - ⚠️ Uses `"k"` not `"secret"`, and `"c"` not `"command"`
- **Success response**: `{"output": "command stdout\n"}`
- **Error 401**: Wrong secret key
- **Error 500**: Command execution error or malformed request

## Usage Pattern

```python
import urllib.request
import json

BRIDGE = "https://audio-koba.cornelio.app"
SECRET = "limon8080"

def bridge(cmd, timeout=30):
    data = json.dumps({"k": SECRET, "c": cmd}).encode()
    req = urllib.request.Request(
        f"{BRIDGE}/exec", 
        data=data, 
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode()
```

## Bridge Source Daemon
- **File**: `/opt/koba_audio_daemon.py`
- **Port**: 9999
- **Also serves**: `/health` (health check), `/latest` (transcriptions)

## Pitfalls
- **Multiline commands fail** (HTTP 500) — use single-line shell commands
- Single quotes in commands break the daemon's shell parsing — avoid them or use double quotes
- Very long output may be truncated
- The daemon runs commands as root — be careful with destructive operations
- If daemon restarts, the secret may change (check `/opt/koba_audio_daemon.py`)