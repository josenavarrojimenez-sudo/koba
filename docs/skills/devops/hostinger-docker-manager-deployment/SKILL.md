---
name: hostinger-docker-manager-deployment
description: Deploy and stabilize custom Docker containers in the Hostinger VPS Docker Manager. Always use the 'Compose' button for UI visibility. For audio transfer to WhatsApp/Telegram from inside a container, map the host's Hermes audio_cache to a container dir and ensure 777 permissions on generated .ogg files so the host-side gateway can read them. Use a persistent sleep command to keep slim images running.
---

# hostinger-docker-manager-deployment

Deploy and stabilize custom Docker containers in the Hostinger VPS Docker Manager. Always use the 'Compose' button for UI visibility. For audio transfer to WhatsApp/Telegram from inside a container, map the host's Hermes audio_cache to a container dir and ensure 777 permissions on generated .ogg files so the host-side gateway can read them. Use a persistent sleep command to keep slim images running.

## Deployment Stability Tips
- **Persistent Shells:** If the container restarts instantly, add `tty: true`, `stdin_open: true`, and `command: /bin/sh -c "while true; do sleep 1000; done"` to the Compose file.
- **Binary Dependencies:** Managed containers often have restricted `apt-get` permissions (setgroups failed). To use `ffmpeg` for OGG/Opus conversion, download a static binary to a persistent volume (e.g., `/home/node/ffmpeg`) rather than trying to install it.
- **Path Discovery:** Hostinger projects aren't always in `/home/docker-projects/`. Use `docker inspect <name> | grep "Source"` to find the real host path if you need to access files via terminal.
- **Visibility:** Projects created via CLI `docker run` may not show up as "Running" in the UI. Always use the "Compose" button in the dashboard to ensure the UI tracks the project status.


## Procedure

### 1. Initial Deployment (Compose)
Use the **Compose** button in the Hostinger panel. To keep the container alive for further interaction/development, use a `tty` or a sleep command.

```yaml
version: '3.8'
services:
  koba-service:
    image: node:18-slim # or your preferred image
    container_name: kebab-case-name
    restart: always
    tty: true
    stdin_open: true
    command: /bin/sh -c "while true; do sleep 1000; done"
    ports:
      - "41607:41607"
    volumes:
      - /data/project/config:/app/config
```

### 2. Handling "Stopped" Status
If the dashboard shows "Stopped" or a gray icon:
- **Check Logs:** Click **Manage** > **Logs** in the UI.
- **Terminal Verify:** Click the **Terminal** button and run:
  ```bash
  docker ps -a
  ```
  If it says `Exited (0)`, the process finished. Use the `command: tail -f /dev/null` or `sleep` trick in the Compose file to keep it up.

### 3. Locating Files on Hostinger VPS
Hostinger's Docker Manager does not always use standard `/home/docker-projects/` paths for all deployments. To find where your `docker-compose.yml` is actually stored:
```bash
find / -name "docker-compose.yml" 2>/dev/null
```
To find the volume source for a specific container:
```bash
docker inspect <container_name> | grep "Source"
```

### 4. Forcing an Update
If the UI is stuck, go to the Terminal and force a rebuild/restart:
```bash
docker compose -f <path_to_yml> up -d --build
```

## Troubleshooting 502 Bad Gateway on Skeleton Containers
When a service behind Cloudflare shows 502 Bad Gateway, follow this diagnostic path:

### 1. Check if the container is actually running the service, not just the skeleton
Skeleton containers (deployed via Compose with `tail -f /dev/null`) appear "Running" in the UI but run no actual application.

```bash
# Check if the container is just a skeleton
docker inspect <container_name> --format='{{json .Config.Cmd}}'
# If output is ["tail","-f","/dev/null"], the real service is NOT running

# Test if something responds on the mapped port
curl -sv http://localhost:<EXTERNAL_PORT>/
# "Connection reset by peer" = something bound but rejects, ECONNREFUSED = nothing listening
```

### 2. Diagnose what's actually running inside
```bash
# Check container state and restart count
docker inspect <container_name> --format='{{.State.Status}} {{.RestartCount}}'

# Try to find the app files (may be in /app/data, /home/node, etc.)
docker exec <container_name> ls /app/ 2>/dev/null || docker exec <container_name> find /home -maxdepth 3 -name "package.json" 2>/dev/null

# Test the internal service
docker exec <container_name> node -e "fetch('http://localhost:<INTERNAL_PORT>/').then(r => r.text()).then(t => console.log(t)).catch(e => console.log('FAILED:', e.message))"
```

### 3. If the skeleton lost the app (files gone, service dead)
The app files were either never persisted to a volume or were lost on container recreation. You need to:
1. Re-clone/build the app from source OR
2. Check if the code exists in a named volume: `docker volume ls | grep kobaco`

## Pitfalls
### YAML Validation Gotchas
- **Trailing Root-Level `volumes:` Dropped**: Hostinger's YAML editor sometimes silently drops the final `volumes:` section. If deployment fails with "undefined volume", verify the file ends with the root-level volumes declaration (NOT indented under `services:`).
- **Inline Comments on Port Mappings**: Lines like `- "3200:3000"  # Panel Web` can cause the Hostinger YAML parser to reject the file. Put comments on their own lines above the value.

## Hostinger VPS Specific Constraints
### Docker Manager UI vs Terminal
- **Project Visibility**: Projects MUST be created via the 'Compose' button in the Hostinger Docker Manager UI to be visible and manageable in the web dashboard. Manual `docker run` or `docker compose` commands in the terminal will result in containers that are "orphaned" from the UI.
- **Service Persistence**: To keep a container 'Running' in the UI when using base images like `node:slim` or `ubuntu`, ensure matches the `command: /bin/sh -c \"while true; do sleep 1000; done\"` or set `tty: true` and `stdin_open: true` in the Compose file.
- **Missing/Private Image Hangs**: If the Compose deployment gets stuck on "Deploying" indefinitely, the Docker image likely doesn't exist publicly (e.g., typos, moved repos) or requires GHCR/private authentication that the Hostinger UI doesn't support.
  - **Verify image existence before using it**: Check Docker Hub API — `curl -s https://hub.docker.com/v2/repositories/{org}/{repo}/`. If it returns 404, the image does NOT exist publicly.
  - **GHCR (GitHub Container Registry) images are NOT accessible** from Hostinger's Docker Manager without authentication. Images like `ghcr.io/paperclipai/paperclip:master` will fail silently.
  - **Fallback Strategy**: Deploy a standard public base image (like `node:lts-slim`, `postgres:alpine`, or `ubuntu`) with `command: tail -f /dev/null`. Once it is visibly "Running" in the UI, use the container's Terminal to manually `git clone`, install dependencies, compile, and launch from source.

### Filesystem & Permissions
- **Execute Permissions (/tmp)**: The `/tmp` directory in Hostinger's managed Docker environment is often mounted with `noexec`. Binaries (like `ffmpeg`) will fail with 'Permission Denied' even if `chmod +x` is applied.
- **Persistent Binaries**: Install static binaries in `/home/node/bin/` or similar home-directory paths to ensure execution permissions and persistence across container restarts.

## WhatsApp Gateway Visibility (Critical)
To ensure the Hermes Messaging Gateway (running outside Docker) can see media generated inside the container:
- **Volume Mapping**: Map the container's output directory to the Gateway's expected cache path:
  `- /home/node/.hermes/audio_cache:/root/.hermes/audio_cache`
- **Output Path**: Save `.ogg` files directly to `/root/.hermes/audio_cache/` inside the container so they instantly replicate to the host's bridge path.
