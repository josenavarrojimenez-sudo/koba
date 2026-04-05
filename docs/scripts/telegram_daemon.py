#!/usr/bin/env python3
"""
Koba Telegram Multi-Bot Daemon v3
- Allowlist de usuarios autorizados
- Ejecuta Hermes CLI con el soul de cada agente
- Responde via Telegram Bot API
"""
import requests
import subprocess
import json
import time
import os
import threading
import re
from datetime import datetime, timezone

# ============================================================
# CONFIGURACION
# ============================================================
ALLOWLIST = {"7666543493"}  # Solo Jose Navarro

BOTS = {
    "Polar":   {"token": "8430244206:AAFDSUjRfVdgaTDVVUeEoZd9yy9SxeYHbvI",  "soul": "/root/koba/agents/polar.md",   "model": "minimax/minimax-m2.5:free"},
    "Lucio":   {"token": "85
13984871:AAHMJ-SLDeS08K_NIiNrwnrVnID9sUhV64w",  "soul": "/root/koba/agents/lucio.md",   "model": "gpt-5.4-mini"},
    "Zantes":  {"token": "8701935729:AAHZI6Fq48Al9oVa7rShM9ffOdmSoqdxr6g",  "soul": "/root/koba/agents/zantes.md",  "model": "gpt-5.4-mini"},
    "Kira":    {"token": "8654506076:AAEFAqtzgkF5GoNKDGVo1xzsuWjMb9htk3s",  "soul": "/root/koba/agents/kira.md",    "model": "gpt-5.4-mini"},
    "Virdon":  {"token": "8764134054:AAGtNbIN_ylKitudP1VO8Fz2NgXFg9XzrFU",  "soul": "/root/koba/agents/virdon.md",  "model": "minimax/minimax-m2.7"},
    "Cornelio":{"token": "8579844363:AAGbRHOsuw3imx7OBxGmmC-rCiioOE24Jjg", "soul": "/root/koba/agents/koba.md",    "model": "qwen/qwen3.6-plus:free"},
 
   "Dalton":  {"token": "8583017482:AAFwTfAQsoLyJZwTQg1R5QMc7oEdfoL1xYE",  "soul": "/root/koba/agents/dalton.md",  "model": "kimi/kimi-k2.5"},
    "Enzo":    {"token": "8676158229:AAFIYuAni04NHagpBIs-o44OiD1_JRah93E",  "soul": "/root/koba/agents/enzo.md",    "model": "minimax/minimax-m2.7"},
    "Apolo":   {"token": "8609432725:AAFezJPpJxArL_EHJqMz5h5HTe5cwbXNREU",  "soul": "/root/koba/agents/apolo.md",   "model": "anthropic/claude-sonnet-4"},
}

TG_API = "https://api.telegram.org/bot{}"
LOG_FILE = "/var/log/koba_telegram.log"
STATE_FILE = "/root/koba/telegram/offsets.json"
HERMES_CLI = "/root/.local/bin/hermes"
CROSS_CHANNEL_STATE = "/root/koba/vault/Inbox/cross-channel-state.json"

os.make
dirs("/root/koba/telegram", exist_ok=True)
os.makedirs("/root/koba/vault/Inbox", exist_ok=True)

# ============================================================
# STATE
# ============================================================
def load_offsets():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_offset(name, offset):
    offsets = load_offsets()
    offsets[name] = offset
    with open(STATE_FILE, "w") as f:
        json.dump(offsets, f)

# ============================================================

def load_cross_channel_state():
    try:
        with open(CROSS_CHANNEL_STATE, "r") as f:
            return json.load(f)

    except:
        return {"channels": {}, "global_threads": [], "last_updated": datetime.now(timezone.utc).isoformat() + "Z"}

def save_cross_channel_state(state):
    state["last_updated"] = datetime.now(timezone.utc).isoformat() + "Z"
    with open(CROSS_CHANNEL_STATE, "w") as f:
        json.dump(state, f, indent=2)

def get_cross_channel_context(current_channel, user_message):
    state = load_cross_channel_state()
    state["channels"][current_channel] = {
        "last_context": user_message,
        "updated_at": datetime.now(timezone.utc).isoformat() + "Z"
    }
    save_cross_channel_state(state)
    cc = []
    for ch, d in state["channels"].items():
        if ch != current_cha
nnel and d.get("last_context"):
            cc.append("[" + ch + "] (" + d.get("updated_at","")[:19] + "): " + d["last_context"][:300])
    if cc:
        return "\n--- CROSS-CHANNEL CONTEXT (other sessions) ---\n" + "\n".join(cc) + "\n--- END CROSS-CHANNEL CONTEXT ---\n"
    return ""

# TELEGRAM API
# ============================================================
def get_updates(token, offset=0, timeout=30):
    url = f"{TG_API.format(token)}/getUpdates"
    try:
        r = requests.get(url, params={"offset": offset, "timeout": timeout}, timeout=timeout+5)
        return r.json().get("result", [])
    except Exception as e:
        log(f"Poll error: {e}")
        return []

def send_message
(token, chat_id, text, reply_to=None):
    url = f"{TG_API.format(token)}/sendMessage"
    if len(text) > 4000:
        text = text[:3990] + "\n[...cortado...]"
    data = {"chat_id": chat_id, "text": text.strip()}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    try:
        r = requests.post(url, json=data, timeout=30)
        return r.json().get("ok", False)
    except Exception as e:
        log(f"Send error: {e}")
        return False

def send_action(token, chat_id, action="typing"):
    url = f"{TG_API.format(token)}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=10)
    except:
        pass

# ==============
==============================================
# LOGGING
# ============================================================
def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass

# ============================================================
# HERMES EXECUTION
# ============================================================
def run_hermes(soul_path, message, model, timeout=120):
    try:
        with open(soul_path) as f:
            soul = f.read()
    except:
        soul = "You are a helpful assistant."

    channel = os.e
nviron.get("KOBACO_CHANNEL", "telegram")
    cross_ctx = get_cross_channel_context(channel, message)
    if cross_ctx:
        prompt = f"Instructions:\n{soul}\n\n{cross_ctx}\n---\nUser says: {message}"
    else:
        prompt = f"Instructions:\n{soul}\n\n---\nUser says: {message}"

    cmd = [
        HERMES_CLI, "chat", "-q", prompt, "-Q",
        "-m", model,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd="/root", env={**os.environ, "HOME": "/root"}
        )
        stdout = result.stdout.strip()
        session_match = re.search(r'\''\nsession_id:\s*(\S+)'\'', stdout)
        if session_match:
            ret
urn stdout[:session_match.start()].strip()
        return stdout or "⚠️ Sin respuesta del agente."
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout. El agente está pensando demasiado."
    except Exception as e:
        log(f"Hermes error: {e}")
        return f"⚠️ Error: {str(e)[:200]}"

# ============================================================
# BOT WORKER
# ============================================================
class BotWorker(threading.Thread):
    def __init__(self, name, token, soul_path, model):
        super().__init__(daemon=True, name=name)
        self.name = name
        self.token = token
        self.soul_path = soul_path
        self.model = model

 
   def run(self):
        log(f"🟢 [{self.name}] Worker iniciando (model={self.model})")
        offset = load_offsets().get(self.name, 0)

        while True:
            try:
                updates = get_updates(self.token, offset=offset + 1, timeout=25)
                for update in updates:
                    offset = max(offset, update["update_id"])
                    save_offset(self.name, offset)

                    msg = update.get("message") or update.get("edited_message")
                    if not msg:
                        continue

                    user_id = str(msg["from"]["id"])
                    # ALLOWLIST CHECK
                    if user_id not in ALLOWLIST:
    
                    log(f"🚫 [{self.name}] BLOCKED user {user_id}")
                        continue

                    text = msg.get("text", "")
                    if not text:
                        continue

                    chat_id = msg["chat"]["id"]
                    message_id = msg.get("message_id")

                    log(f"📨 [{self.name}] From Jose ({user_id}): {text[:80]}")

                    # Typing indicator
                    send_action(self.token, chat_id, "typing")

                    # Run Hermes
                    response = run_hermes(self.soul_path, text, self.model)

                    log(f"📤 [{self.name}] Sending response ({len(response)} chars)")
   
                 send_message(self.token, chat_id, response, reply_to=message_id)

            except Exception as e:
                log(f"❌ [{self.name}] Error: {e}")
                time.sleep(10)

            time.sleep(1)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    log("=" * 60)
    log("🚀 Koba Telegram Multi-Bot Daemon v3")
    log(f"🔒 Allowlist: {ALLOWLIST}")
    log(f"📋 Bots: {list(BOTS.keys())}")

    threads = []
    for name, cfg in BOTS.items():
        w = BotWorker(name, cfg["token"], cfg["soul"], cfg["model"])
        w.start()
        threads.append(w)
    
    time.sleep(1)

    log(f"✅ {len(threads)} bots online. Polling...")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        log("🛑 Shutdown")


