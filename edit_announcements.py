#!/usr/bin/env python3
"""
CS2 Server Announcement Editor (CLI)
=====================================
Interactive CLI tool to view, add, edit, remove, and deploy in-game rotating
chat announcements for the 'ServerAnnouncer' plugin on your CS2 server.
Automatically updates the server configuration and hot-reloads via RCON.
"""

import sys
import json
import socket
import struct

try:
    import paramiko
except ImportError:
    print("[ERROR] 'paramiko' is required. Run: pip install paramiko")
    sys.exit(1)

SERVER_HOST = "81.181.113.120"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = ")(e092e8EjTUiV"
RCON_PORT = 27015
RCON_PASS = "walliez_rcon_2026"
REMOTE_CONFIG_PATH = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/ServerAnnouncer/ServerAnnouncer.json"

COLOR_PREVIEW_MAP = {
    "{Default}": "\033[0m",
    "{White}": "\033[97m",
    "{Red}": "\033[91m",
    "{Green}": "\033[92m",
    "{LightYellow}": "\033[93m",
    "{LightBlue}": "\033[94m",
    "{LightPurple}": "\033[95m",
    "{Gold}": "\033[33m",
    "{Lime}": "\033[92m",
    "{Grey}": "\033[90m"
}

def render_preview(text: str) -> str:
    rendered = text
    for tag, ansi in COLOR_PREVIEW_MAP.items():
        rendered = rendered.replace(tag, ansi)
    return rendered + "\033[0m"

def get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=10)
    return ssh

def fetch_config():
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_CONFIG_PATH, 'r') as f:
        data = f.read().decode('utf-8')
    sftp.close()
    ssh.close()
    # Strip any potential leading comment lines
    lines = [line for line in data.splitlines() if not line.strip().startswith("//")]
    return json.loads("\n".join(lines))

def save_and_reload(cfg_data):
    print("\n[*] Saving updated configuration to server...")
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_CONFIG_PATH, 'w') as f:
        json.dump(cfg_data, f, indent=2)
    sftp.close()
    ssh.close()
    print("[+] Configuration successfully saved to VPS.")

    print("[*] Hot-reloading ServerAnnouncer plugin via RCON...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect((SERVER_HOST, RCON_PORT))
        pwd = RCON_PASS
        s.send(struct.pack('<iii', len(pwd) + 10, 1, 3) + pwd.encode('ascii') + b'\x00\x00')
        s.recv(4096)
        cmd = 'css_plugins reload ServerAnnouncer'
        s.send(struct.pack('<iii', len(cmd) + 10, 2, 2) + cmd.encode('ascii') + b'\x00\x00')
        out = s.recv(4096)
        s.close()
        print("[+] Plugin successfully reloaded live on the server!")
    except Exception as e:
        print(f"[!] Warning reloading via RCON: {e}")

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 65)
    print("      CS2 Live In-Game Announcement Editor")
    print("=" * 65)
    print(f"[*] Fetching active announcements from {SERVER_HOST}...")

    try:
        cfg = fetch_config()
    except Exception as e:
        print(f"[ERROR] Could not fetch configuration: {e}")
        return

    dirty = False

    while True:
        interval = cfg.get("IntervalSeconds", 90)
        prefix = cfg.get("Prefix", "{Gold}★ {LightBlue}[Walliez]{Default}")
        random_order = cfg.get("RandomOrder", True)
        messages = cfg.get("Messages", [])

        print("\n" + "-" * 65)
        print(f" Current Settings:")
        print(f"   [1] Interval:       {interval} seconds")
        print(f"   [2] Random Order:   {'Enabled' if random_order else 'Disabled (Sequential)'}")
        print(f"   [3] Message Prefix: {prefix}")
        print(f"       Preview:        {render_preview(prefix)}")
        print("-" * 65)
        print(" Active Rotating Messages:")
        for i, msg in enumerate(messages, 1):
            print(f"   [{i}] Raw:     {msg}")
            print(f"       Preview: {render_preview(prefix + ' ' + msg)}")
        print("-" * 65)

        print("\nActions:")
        print("   [A] Add new announcement message")
        print("   [E] Edit an existing message")
        print("   [D] Delete a message")
        print("   [T] Change interval timer")
        print("   [P] Change prefix")
        print("   [R] Toggle random/sequential rotation")
        print("   [S] Save and Deploy to live server")
        print("   [Q] Quit without saving")

        choice = input("\nSelect an action: ").strip().upper()

        if choice == 'A':
            print("\nAvailable color tags: {Default}, {White}, {Red}, {Green}, {LightYellow}, {LightBlue}, {LightPurple}, {Gold}, {Lime}, {Grey}")
            new_msg = input("Enter new announcement text:\n> ").strip()
            if new_msg:
                messages.append(new_msg)
                cfg["Messages"] = messages
                dirty = True
                print("[+] Added new message.")

        elif choice == 'E':
            if not messages:
                print("[!] No messages to edit.")
                continue
            idx_str = input(f"Enter message number to edit (1-{len(messages)}): ").strip()
            if idx_str.isdigit():
                idx = int(idx_str) - 1
                if 0 <= idx < len(messages):
                    print(f"Current: {messages[idx]}")
                    edit_msg = input("New text (or press Enter to cancel):\n> ").strip()
                    if edit_msg:
                        messages[idx] = edit_msg
                        cfg["Messages"] = messages
                        dirty = True
                        print("[+] Message updated.")

        elif choice == 'D':
            if not messages:
                print("[!] No messages to delete.")
                continue
            idx_str = input(f"Enter message number to delete (1-{len(messages)}): ").strip()
            if idx_str.isdigit():
                idx = int(idx_str) - 1
                if 0 <= idx < len(messages):
                    removed = messages.pop(idx)
                    cfg["Messages"] = messages
                    dirty = True
                    print(f"[+] Deleted message: {removed}")

        elif choice == 'T':
            new_int = input(f"Enter announcement interval in seconds (current: {interval}): ").strip()
            if new_int.isdigit() and int(new_int) > 0:
                cfg["IntervalSeconds"] = int(new_int)
                dirty = True
                print(f"[+] Interval updated to {new_int}s.")

        elif choice == 'P':
            new_pref = input("Enter new announcement prefix:\n> ").strip()
            if new_pref:
                cfg["Prefix"] = new_pref
                dirty = True
                print("[+] Prefix updated.")

        elif choice == 'R':
            cfg["RandomOrder"] = not random_order
            dirty = True
            print(f"[+] Random order set to: {cfg['RandomOrder']}")

        elif choice == 'S':
            save_and_reload(cfg)
            dirty = False
            input("\nPress Enter to continue...")

        elif choice == 'Q':
            if dirty:
                confirm = input("You have unsaved changes. Really quit? [y/N]: ").strip().lower()
                if confirm == 'y':
                    break
            else:
                break

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
