#!/usr/bin/env python3
"""
CS2 Server Name / Hostname Updater
Updates the server title immediately via RCON and permanently in server.cfg.
"""

import sys
import os
import re
import socket
import struct
import time

try:
    import paramiko
except ImportError:
    print("[ERROR] 'paramiko' is required. Run: pip install paramiko")
    input("\nPress Enter to exit...")
    sys.exit(1)

# ================= Configuration =================
SERVER_HOST = "81.181.113.120"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = ")(e092e8EjTUiV"

RCON_PORT = 27015
RCON_PASS = "walliez_rcon_2026"

REMOTE_CFG_PATH = "/home/csgoserver/server-cs2/game/csgo/cfg/server.cfg"


def get_current_hostname_a2s():
    """Query current server hostname via Source A2S_INFO."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.5)
        query = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(query, (SERVER_HOST, RCON_PORT))
        resp, _ = sock.recvfrom(4096)
        
        # Handle challenge response if needed
        if resp.startswith(b'\xFF\xFF\xFF\xFF\x41'):
            challenge = resp[5:9]
            sock.sendto(query + challenge, (SERVER_HOST, RCON_PORT))
            resp, _ = sock.recvfrom(4096)
        
        sock.close()
        if resp.startswith(b'\xFF\xFF\xFF\xFFI'):
            name_end = resp.find(b'\x00', 6)
            if name_end != -1:
                return resp[6:name_end].decode('utf-8', errors='ignore')
    except Exception:
        pass
    return None


def rcon_exec(command):
    """Execute command on live CS2 server via Source RCON."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.5)
    try:
        s.connect((SERVER_HOST, RCON_PORT))
        # Auth packet
        auth_data = struct.pack('<iii', len(RCON_PASS) + 10, 1, 3) + RCON_PASS.encode('ascii') + b'\x00\x00'
        s.send(auth_data)
        resp = s.recv(4096)
        if len(resp) < 12:
            return False, "RCON auth failed: invalid response"
        resp_id = struct.unpack('<iii', resp[:12])[1]
        if resp_id == -1:
            return False, "RCON auth rejected: bad password"

        # Exec packet
        cmd_bytes = command.encode('utf-8')
        exec_data = struct.pack('<iii', len(cmd_bytes) + 10, 2, 2) + cmd_bytes + b'\x00\x00'
        s.send(exec_data)

        out = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                out += chunk
                if len(chunk) < 4096:
                    break
            except socket.timeout:
                break
        return True, out
    except Exception as e:
        return False, str(e)
    finally:
        s.close()


def update_server_cfg(new_name):
    """Update or prepend hostname line in remote server.cfg via SFTP."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=10)
    
    sftp = ssh.open_sftp()
    try:
        try:
            with sftp.open(REMOTE_CFG_PATH, 'r') as f:
                content = f.read().decode('utf-8')
        except FileNotFoundError:
            content = ""

        # Safe escape double quotes for CFG
        escaped_name = new_name.replace('"', '\\"')
        hostname_line = f'hostname "{escaped_name}"'

        # Check if hostname already exists
        if re.search(r'^\s*hostname\s+.*$', content, flags=re.MULTILINE):
            new_content = re.sub(r'^\s*hostname\s+.*$', hostname_line, content, flags=re.MULTILINE)
        else:
            # Prepend hostname at the top of server.cfg
            new_content = f"{hostname_line}\n\n{content}"

        with sftp.open(REMOTE_CFG_PATH, 'w') as f:
            f.write(new_content)
        
        # Ensure correct ownership and permissions
        sftp.close()
        ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_CFG_PATH} && chmod 664 {REMOTE_CFG_PATH}")
    finally:
        ssh.close()


def apply_hostname(new_name):
    new_name = new_name.strip()
    if not new_name:
        print("[ERROR] Server name cannot be empty.")
        return False

    print(f"\n[1/3] Updating live server via RCON to: \"{new_name}\" ...")
    escaped_rcon = new_name.replace('"', '\\"')
    success, err = rcon_exec(f'hostname "{escaped_rcon}"')
    if success:
        print("      [OK] RCON updated live server successfully!")
    else:
        print(f"      [WARN] Could not update live RCON: {err}")
        print("      (The change will still take effect after map change or restart)")

    print(f"[2/3] Writing permanent setting to remote server.cfg ...")
    try:
        update_server_cfg(new_name)
        print(f"      [OK] Saved to {REMOTE_CFG_PATH}")
    except Exception as e:
        print(f"      [ERROR] Failed to write server.cfg: {e}")
        return False

    print(f"[3/3] Verifying public server broadcast (A2S_INFO query) ...")
    time.sleep(1.2)
    verified_name = get_current_hostname_a2s()
    if verified_name:
        print(f"      [OK] Server is now publicly broadcasting as:")
        print(f"      >>> {verified_name} <<<")
    else:
        print("      [INFO] Server name written. Query timed out (server might still be processing).")

    print("\n[SUCCESS] Server name has been updated successfully!")
    return True


def main():
    print("=" * 60)
    print("      CS2 Dedicated Server Name / Hostname Updater")
    print("=" * 60)

    current_name = get_current_hostname_a2s()
    if current_name:
        print(f"Current server title: \"{current_name}\"")
    else:
        print("Current server title: (Server query offline or unreachable)")

    if len(sys.argv) > 1:
        new_name = " ".join(sys.argv[1:])
    else:
        print("\nEnter your new server name (or press Enter to cancel):")
        try:
            new_name = input("New Title: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)

    if not new_name:
        print("No name entered. Exiting.")
        sys.exit(0)

    apply_hostname(new_name)


if __name__ == "__main__":
    main()
