---
name: hostinger-post-deploy-ssh-setup
description: Deploy a skeleton container via Compose (to get it Running in UI), then SSH into the Hostinger VPS to manually set up the real project inside — cloning repos, installing deps, compiling, launching servers, and connecting networks. Use when Compose-based image pull fails or the source project requires building from code.
---

# hostinger-post-deploy-ssh-setup

Deploy a skeleton container in Hostinger's Docker Manager, then SSH in to do the real work.

## When to Use
- The target project has no public Docker image (only source code)
- Hostinger's Docker Manager can't pull GHCR or private registry images
- Compose deployments keep hanging on image pull

## Procedure

### Step 1: Deploy a Skeleton via Compose
Use the 'Compose' button with a minimal YAML that will **always** pull successfully:

```yaml
services:
  my-project:
    image: node:lts-trixie-slim
    container_name: my-project-1
    restart: always
    command: tail -f /dev/null
    ports:
      - "EXTERNAL_PORT:INTERNAL_PORT"
    volumes:
      - my_project_data:/app/data

volumes:
  my_project_data:
```

### Step 2: SSH into the Hostinger VPS
```python
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=22, username='root', password='YOUR_PASSWORD')
```

### Step 3: Install Tools Inside the Container
```bash
docker exec my-project-1 bash -c "
apt-get update && apt-get install -y git ripgrep curl &&
corepack enable pnpm
"
```

### Step 4: Clone the Project
```bash
docker exec my-project-1 bash -c "
cd /app/data &&
git clone https://github.com/org/repo.git repo
"
```

### Step 5: Install Dependencies and Build
```bash
docker exec my-project-1 bash -c "
cd /app/data/repo &&
pnpm install 2>&1 | tail -20 &&
pnpm --filter @scope/ui build &&
pnpm --filter @scope/server build &&
test -f server/dist/index.js && echo 'BUILD SUCCESS'
"
```

### Step 6: Launch the Server
```bash
docker exec my-project-1 bash -c "
export DATABASE_URL='postgres://user:pass@hostname:5432/db'
export BETTER_AUTH_SECRET='your_secret'
export PORT=3100
export HOST=0.0.0.0
export SERVE_UI=true

cd /app/data/repo
nohup node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js > /app/data/server.log 2>&1 &
echo SERVER_PID=\$!
sleep 8
# Check if running
kill -0 \$! 2>/dev/null && echo 'Server is running!' || tail -50 /app/data/server.log
"
```

### Step 7: If Multi-Container (e.g., needs Postgres)
Run Postgres as a separate container:
```bash
docker run -d --name my-project-db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=db postgres:17-alpine
```

**CRITICAL**: Connect it to the same Docker network so containers can resolve each other by hostname:
```bash
# Find the network name of the skeleton container
docker inspect my-project-1 --format '{{json .NetworkSettings.Networks}}'
# Connect the DB container to that network
docker network connect skeleton_network_name my-project-db
```

## Pitfalls
- **Network Isolation**: `docker run` creates containers on `bridge` by default, while Compose creates a named network (`project_default`). Containers on different networks cannot resolve each other by hostname. Always use `docker network connect` after creating the DB container.
- **Container Command Parsing**: When running complex multi-line commands via `docker exec bash -c`, variable expansion can behave unexpectedly. Use simple `export` + `cd` + `nohup` patterns.
- **Python paramiko in Hermes**: paramiko must be installed via `pip3 install paramiko` before use, as it is not pre-installed in the Hermes sandbox. Import must be inside `python3 -c` blocks, not in `execute_code` scripts.
- **Kill orphan processes**: If restarting the app server, kill the old one first: `kill $(pgrep -f 'node.*server')`.
