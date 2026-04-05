#!/usr/bin/env python3
"""Agent Task Auditor - Logs every task execution"""
import json
import os
from datetime import datetime, timezone

LOG_FILE = "/root/koba/logs/task-log.json"

def log_task(agent, action, status, details="", task_id=None):
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump({"tasks": []}, f)
    
    with open(LOG_FILE, "r") as f:
        data = json.load(f)
    
    import hashlib
    tid = task_id or hashlib.md5(f"{agent}{action}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    data["tasks"].append({
        "task_id": tid,
        "agent": agent,
        "action": action,
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Keep last 100 tasks
    data["tasks"] = data["tasks"][-100:]
    
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    return tid

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        agent, action, status = sys.argv[1], sys.argv[2], sys.argv[3]
        details = sys.argv[4] if len(sys.argv) > 4 else ""
        tid = log_task(agent, action, status, details)
        print(f"Logged: {tid}")
    else:
        print("Usage: auditor.py <agent> <action> <status> [details]")

