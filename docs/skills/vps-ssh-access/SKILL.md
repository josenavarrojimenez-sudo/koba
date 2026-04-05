---
name: vps-ssh-access
category: devops
description: Connect to Jose Navarro's Hostinger VPS via SSH key authentication - access Docker containers and Paperclip database.
---

# VPS SSH Access

Connect to Jose Navarro's Hostinger VPS via SSH key authentication.

## Connection Details

- **Host:** `srv1443323.hstgr.cloud`
- **Port:** `22`
- **User:** `root`
- **Auth:** SSH Ed25519 key at `~/.ssh/vps_key_ed25519`

## Quick Connect via paramiko

```python
import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(
    os.path.expanduser("~/.ssh/vps_key_ed25519"))
ssh.connect('srv1443323.hstgr.cloud', 22, 'root', pkey=key, timeout=15)

stdin, stdout, stderr = ssh.exec_command('docker ps')
print(stdout.read().decode())
ssh.close()
```

## Quick Connect via subprocess (ssh command)

```bash
ssh -i ~/.ssh/vps_key_ed25519 -o StrictHostKeyChecking=no root@srv1443323.hstgr.cloud "docker ps"
```

## Running Docker Commands

The VPS runs Docker containers. Key containers:
- `paperclip-paperclip-1` — Paperclip app server
- `kobaco-db` — PostgreSQL database (user: paperclip, db: paperclip)
- `kobaco-paperclip-1` — Paperclip instance for Kobaco
- `cloudflared-kobaco` — Cloudflare tunnel
- `hermes-*` — Hermes gateway
- `koba-final`, `koba-final-manager` — Koba services

To run commands inside containers:
```bash
docker exec kobaco-db psql -U paperclip -d paperclip -c "SQL_HERE"
```

## Fallback (password auth)

If for some reason key auth fails (e.g., key file missing):
- **Password:** `limon8080G#CR`
- Then regenerate keys: `ssh-keygen -t ed25519` and add to `~/.ssh/authorized_keys`

## Pitfalls
- **paramiko not installed:** Run `pip install paramiko -q` first
- **RSA keys fail:** The VPS only accepts ed25519, not RSA
- **Shell escaping:** When passing SQL through docker exec, use single quotes or escape properly
- **The .ssh directory** must have 700 permissions, authorized_keys must have 600
- **Sandboxes don't persist files:** The SSH key needs to be in place on the current sandbox. If ~/.ssh/vps_key_ed25519 doesn't exist, regenerate (use fallback password) and add it again.