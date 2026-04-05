---
name: openclaw-config-troubleshooting
description: Troubleshooting and manual fixing of OpenClaw agent configuration errors, specifically focusing on gateway.bind validation issues in Docker environments where standard CLI fixes (doctor --fix) might fail.
---

# openclaw-config-troubleshooting

Use this skill when an OpenClaw agent fails to start due to invalid configuration, particularly the `gateway.bind` property, or when `openclaw doctor --fix` fails to resolve the issue.

## Diagnosis
- **Error Signatures**: 
  - `gateway.bind: Invalid input (allowed: "auto", "lan", "loopback", "custom", "tailnet")`
  - `Config invalid` or `Invalid config at /home/node/.openclaw/openclaw.json`
- **Context**: Often occurs after automated updates or manual edits that introduce unrecognized bind strings.

## Procedure

### 1. Manual JSON Repair (Host/Terminal)
If you have access to the host but cannot use the interactive CLI inside the container, use `sed` to force the bind value to a known safe state (`auto`).

```bash
# Replace [container_name] with the actual Docker container ID/name
docker exec [container_name] sed -i 's/"bind": "[^"]*"/"bind": "auto"/' /home/node/.openclaw/openclaw.json
```

### 2. Verification and Restart
After the manual patch, restart the container to apply changes.

```bash
docker restart [container_name]
# Verify status
docker exec [container_name] openclaw status
```

### 3. Common Path Locations
If `/home/node/.openclaw/openclaw.json` is not found, check these alternative paths:
- `/root/.openclaw/openclaw.json`
- `~/.openclaw/openclaw.json`

## Pitfalls
- **doctor --fix Failure**: Sometimes the `doctor --fix` command itself fails to run because the config validation happens before the doctor command can execute its logic. Manual file editing is the only path in these cases.
- **Permission Denied**: In Hostinger or restricted VPS environments, ensure you are running commands with sufficient privileges or via the specific `docker exec` bridge.
- **Docker Command Availability**: If `docker` is not available in your current session context but you are on a managed VPS like Hostinger, the user must execute the command in the main server terminal.
