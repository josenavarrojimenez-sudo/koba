---
name: koba-obsidian-vault-sync
category: koba-infra
description: Set up and maintain a PARA-structured Obsidian vault synced between the VPS, GitHub, and the user's local Obsidian client via Git.
---

# Koba Obsidian Vault Sync

## Architecture
```
User Obsidian (Mac)  <--Git-->  GitHub Repo  <--Git Cron (5min)-->  VPS /root/koba/vault/
```

- **VPS**: Agents read/write to `/root/koba/vault/` (PARA structure).
- **GitHub**: `josenavarrojimenez-sudo/koba-vault` (private repo).
- **User Mac**: Obsidian opens `~/Documents/KobaCo` as vault.
- **Obsidian Git Plugin**: Auto-commits every 5 min, auto-pushes.

## Vault Structure (PARA)
```
/root/koba/vault/
├── 1.Projects/       ← Active projects with _TEMPLATE.md
├── 2.Areas/          ← Ongoing responsibilities
├── 3.Resources/      ← Reference material
├── 4.Archive/        ← Completed/inactive
├── Daily Notes/      ← YYYY-MM-DD.md
├── Memory/           ← Long-term memory files
├── AGENTS.md         ← Standing instructions for all agents
├── MEMORY.md         ← Shared long-term memory
└── .obsidian/        ← Obsidian config (includes Git plugin settings)
```

## Sync Flow

### VPS → GitHub (auto, every 5 min)
Cron job runs `/root/koba/scripts/vault-sync.sh`:
```bash
cd /root/koba/vault
git pull --rebase origin main 2>/dev/null || true
git add -A
if git diff --cached --quiet; then
    echo "[$(date)] No changes" >> /var/log/koba_vault_sync.log
else
    git commit -m "$(date '+%Y-%m-%d %H:%M') - auto-sync from agents"
    git push origin main
fi
```

### User Mac → GitHub (Obsidian Git plugin)
Plugin settings in `.obsidian/plugins/obsidian-git/data.json`:
- `autoSaveInterval`: 5
- `autoPullOnBoot`: true
- `disablePush`: false
- `pullBeforePush`: true
- `syncMethod`: "rebase"
- `commitMessage`: "vault backup: {{date}}"

### Agents → Vault
All agents have vault instructions in their `.md` files:
- Path: `/root/koba/vault/`
- Rules: Write work, read context before acting, follow AGENTS.md

## Setup (New Environment)

### 1. Create vault structure on VPS
```bash
mkdir -p /root/koba/vault/{1.Projects,2.Areas,3.Resources,4.Archive,"Daily Notes",Memory}
cd /root/koba/vault
git init
# Add AGENTS.md, templates, etc.
git add -A
git commit -m "Initial vault"
git remote add origin https://{GITHUB_TOKEN}@github.com/{USER}/{REPO}.git
git push -u origin main
```

### 2. Install vault-sync.sh as cron
```bash
(crontab -l 2>/dev/null; echo '*/5 * * * * /root/koba/scripts/vault-sync.sh') | crontab -
```

### 3. User Mac setup
```bash
git clone https://{GITHUB_TOKEN}@github.com/{USER}/{REPO}.git ~/Documents/KobaCo
# Open ~/Documents/KobaCo as Obsidian vault
# Install "Git" plugin by Vinzent (Community Plugins)
# Authorize and enable auto-backup
```

## Conflict Resolution

### When Obsidian Git UI gets stuck (happens often)
The Obsidian Git plugin frequently gets confused with rebases and opens a "conflict-files-obsidian-git" help note. **Do NOT try to resolve via the UI** — it often makes things worse.

**The reliable fix via terminal:**
```bash
# 1. Close Obsidian completely (Cmd+Q) — the plugin fights with the CLI
cd ~/Documents/KobaCo

# 2. Abort any stuck rebase
git rebase --abort

# 3. Pull keeping local version (Mac wins conflicts)
git pull origin main -X ours

# 4. Push
git push
```

### If "detached HEAD" state occurs:
```bash
git checkout -B main && git push -u origin main
```

### If "not currently on a branch" during push:
```bash
git checkout -B main && git push -u origin main
```

### Common conflict: `.obsidian/app.json` and `.obsidian/workspace.json`
These ALWAYS conflict when both sides write config simultaneously. Always accept local (user's Obsidian config) with `-X ours`.

### Key rule: Close Obsidian before running terminal git commands.

## How Agents Use the Vault
All agent `.md` files include:
```
## 🧠 VAULT DE CONOCIMIENTO (PARA)
- Path: /root/koba/vault/
- Structure: 1.Projects, 2.Areas, 3.Resources, 4.Archive, Daily Notes, Memory
- Rule: If you do work, write it to the vault. If there's context, read it before acting.
- AGENTS.md: At the root of the vault. Always read before acting.
```

## Pitfalls
- **Git conflicts** happen if VPS and Mac commit simultaneously — the cron does `pull --rebase` first to minimize this
- **`.obsidian/` files** should NOT be edited by agents — they're Obsidian's internal config
- **Unzip may not be installed** on VPS — can't install Obsidian Git plugin from VPS; user must install from Obsidian UI
- **Token in git remote URL** — if token is rotated, update the remote: `git remote set-url origin https://{NEW_TOKEN}@github.com/...`
- **Daily Notes** should be created by agents with `{{DATE}}` format — Obsidian's Daily Notes plugin can also handle this