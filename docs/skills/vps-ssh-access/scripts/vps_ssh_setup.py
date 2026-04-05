#!/usr/bin/env python3
"""Auto-setup VPS SSH access paramiko key authentication.
Run this at the start of any sandbox to ensure SSH key auth works.
"""
import paramiko, subprocess, os, sys

HOST = 'srv1443323.hstgr.cloud'
USER = 'root'
PASSWORD = 'limon8080G#CR'
KEY_DIR = os.path.expanduser("~/.ssh")
KEY_FILE = os.path.join(KEY_DIR, "vps_key_ed25519")

def try_key_auth():
    """Try connecting with existing ed25519 key."""
    if not os.path.isfile(KEY_FILE):
        return False
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
        ssh.connect(HOST, 22, USER, pkey=key, timeout=10)
        ssh.close()
        return True
    except Exception:
        return False

def generate_and_deploy_key():
    """Generate new ed25519 key, connect via password, deploy public key."""
    os.makedirs(KEY_DIR, exist_ok=True)
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-f", KEY_FILE, "-N", "", "-q"],
        check=True
    )
    with open(KEY_FILE + ".pub") as f:
        pub = f.read().strip()
    
    # Connect via password and deploy
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, 22, USER, PASSWORD, timeout=15)
    cmd = f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    ssh.close()
    
    # Verify
    return try_key_auth()

if __name__ == "__main__":
    if try_key_auth():
        print("SSH key auth OK")
    elif generate_and_deploy_key():
        print("SSH key auth configured successfully")
    else:
        print("FAILED to configure SSH key auth", file=sys.stderr)
        sys.exit(1)
