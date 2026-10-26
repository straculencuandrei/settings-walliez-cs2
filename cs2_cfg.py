#!/usr/bin/env python3
"""
CS2 Gamemode & Server CFG Manager
Search, view, and modify CS2 server convar settings in real time.
"""

import sys
import os
import re
import socket
import struct
import datetime

try:
    import paramiko
except ImportError:
    print("[ERROR] 'paramiko' is required. Run: pip install paramiko")
    sys.exit(1)

# ================= Configuration =================
SERVER_HOST = "81.181.113.120"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = ")(e092e8EjTUiV"

RCON_PORT = 27015
RCON_PASS = "walliez_rcon_2026"

REMOTE_CFG_DIR = "/home/csgoserver/server-cs2/game/csgo/cfg"

# Map game_type / game_mode to CFG filenames
GAMEMODE_MAP = {
    (0, 0): "gamemode_casual.cfg",
    (0, 1): "gamemode_competitive.cfg",
    (0, 2): "gamemode_competitive2v2.cfg",
    (1, 0): "gamemode_armsrace.cfg",
    (1, 1): "gamemode_demolition.cfg",
    (1, 2): "gamemode_deathmatch.cfg",
}

POPULAR_SETTINGS = [
    ("mp_roundtime_defuse", "Round time for bomb defusal maps (minutes, e.g. 1.92 = 1m 55s, 2 = 2m)"),
    ("mp_roundtime", "General round time (minutes)"),
    ("mp_roundtime_hostage", "Round time for hostage maps (minutes)"),
    ("mp_maxrounds", "Maximum total rounds in a match (e.g. 24 for MR12, 30 for MR15)"),
    ("mp_freezetime", "Freeze time at round start in seconds (default 15)"),
    ("mp_buytime", "Buy time in seconds at round start (default 20)"),
    ("mp_startmoney", "Starting money for players (default 800)"),
    ("mp_maxmoney", "Maximum money a player can hold (default 16000)"),
    ("mp_c4timer", "Time in seconds before bomb explodes (default 40)"),
    ("mp_warmuptime", "Warmup period duration in seconds"),
    ("mp_overtime_enable", "Enable overtime if match ends in a tie (1 = yes, 0 = no)"),
    ("mp_overtime_maxrounds", "Number of rounds per overtime (default 6 for 3+3)"),
    ("mp_friendlyfire", "Enable friendly fire (1 = yes, 0 = no)"),
    ("mp_halftime", "Switch teams at halftime (1 = yes, 0 = no)"),
    ("mp_halftime_pausetimer", "Pause duration at halftime in seconds (default 15)"),
    ("mp_match_can_clinch", "Team can win match early if they reach winning round count (1 = yes, 0 = no)"),
]

# ================= RCON Helper =================
def rcon_exec(command):
    """Execute command on live CS2 server via Source RCON."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.5)
    try:
        s.connect((SERVER_HOST, RCON_PORT))
        # Auth packet
        auth_data = struct.pack('<iii', len(RCON_PASS) + 10, 1, 3) + RCON_PASS.encode('ascii') + b'\x00\x00'
        s.send(auth_data)
        resp = s.recv(4096)
        if len(resp) < 12:
            return None
        resp_id = struct.unpack('<iii', resp[:12])[1]
        if resp_id == -1:
            return None

        # Exec packet
        exec_data = struct.pack('<iii', len(command) + 10, 2, 2) + command.encode('ascii') + b'\x00\x00'
        s.send(exec_data)

        out = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                out += chunk
                if len(chunk) < 4096: break
            except socket.timeout:
                break

        if len(out) >= 12:
            body = out[12:-2].decode('utf-8', errors='ignore').strip()
            return body
        return out.decode('utf-8', errors='ignore').strip()
    except Exception:
        return None
    finally:
        s.close()

def get_live_convar(convar_name):
    """Fetch convar value from running server."""
    res = rcon_exec(convar_name)
    if not res:
        return "Unknown (RCON inactive)"
    # Server typically outputs "convar = value" or "convar is value"
    for line in res.splitlines():
        line = line.strip()
        if "=" in line and convar_name.lower() in line.lower():
            parts = line.split("=", 1)
            return parts[1].strip()
        if " is " in line and convar_name.lower() in line.lower():
            return line
    return res.strip()

# ================= SSH & CFG Helpers =================
def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=8)
    return ssh

def detect_active_gamemode(ssh):
    """Inspect cs2 command line to find active gamemode and cfg."""
    _, stdout, _ = ssh.exec_command("ps aux | grep -v grep | grep '/cs2 ' || cat /etc/systemd/system/cs2.service")
    out = stdout.read().decode('utf-8', errors='ignore')
    
    gt_match = re.search(r'\+game_type\s+(\d+)', out)
    gm_match = re.search(r'\+game_mode\s+(\d+)', out)

    gt = int(gt_match.group(1)) if gt_match else 0
    gm = int(gm_match.group(1)) if gm_match else 1
    
    cfg_name = GAMEMODE_MAP.get((gt, gm), "gamemode_competitive.cfg")
    return cfg_name, (gt, gm)

def read_cfg(ssh, filename):
    """Read full cfg file from server."""
    remote_path = f"{REMOTE_CFG_DIR}/{filename}"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote_path, 'r') as f:
            content = f.read().decode('utf-8', errors='ignore')
            return content
    except FileNotFoundError:
        return ""
    finally:
        sftp.close()

def write_cfg_with_backup(ssh, filename, content):
    """Write cfg file to server with an automatic timestamped backup."""
    remote_path = f"{REMOTE_CFG_DIR}/{filename}"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{remote_path}.{timestamp}.bak"
    
    sftp = ssh.open_sftp()
    # Backup existing
    try:
        with sftp.file(remote_path, 'r') as rf, sftp.file(backup_path, 'w') as wf:
            wf.write(rf.read())
    except Exception:
        pass

    with sftp.file(remote_path, 'w') as f:
        f.write(content.encode('utf-8'))
    sftp.close()
    
    # Fix ownership
    ssh.exec_command(f"chown csgoserver:csgoserver {remote_path} && chmod 644 {remote_path}")
    return backup_path

def parse_cfg_lines(content):
    """Parse cfg content into a list of parsed items."""
    parsed = []
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("//"):
            parsed.append({"type": "comment", "raw": line})
            continue

        # Check for command + value + optional comment
        # Format: convar value // comment
        match = re.match(r'^([a-zA-Z0-9_]+)\s+("[^"]*"|\S+)(.*)$', trimmed)
        if match:
            cmd = match.group(1)
            val = match.group(2).strip('"')
            comment = match.group(3).strip()
            parsed.append({
                "type": "convar",
                "cmd": cmd,
                "val": val,
                "comment": comment,
                "raw": line
            })
        else:
            parsed.append({"type": "other", "raw": line})
    return parsed

# ================= Actions =================
def search_in_cfg(parsed_lines, query, fetch_live=True):
    """Search for convars matching query."""
    q = query.lower()
    results = []
    for i, item in enumerate(parsed_lines):
        if item["type"] == "convar":
            if q in item["cmd"].lower() or (item["comment"] and q in item["comment"].lower()):
                results.append((i, item))
    return results

def modify_convar(parsed_lines, target_cmd, new_val):
    """Update convar value in parsed lines, or append if missing."""
    target_lower = target_cmd.lower()
    found = False
    new_lines = []

    for item in parsed_lines:
        if item["type"] == "convar" and item["cmd"].lower() == target_lower:
            old_val = item["val"]
            comment = item["comment"]
            # Preserve comment spacing if exists
            formatted_comment = f"\t\t{comment}" if comment else ""
            item["val"] = str(new_val)
            item["raw"] = f"{target_cmd}\t\t\t\t\t\t\t\t\t{new_val}{formatted_comment}"
            found = True
        new_lines.append(item["raw"])

    if not found:
        new_lines.append(f"\n// Added by CS2 CFG Manager ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        new_lines.append(f"{target_cmd}\t\t\t\t\t\t\t\t\t{new_val}")

    return "\n".join(new_lines), found

# ================= CLI & Interactive UI =================
def print_header(active_cfg):
    print("=" * 72)
    print("           COUNTER-STRIKE 2 — GAMEMODE & CFG MANAGER")
    print(f"  Target Server: {SERVER_HOST}:{RCON_PORT}")
    print(f"  Active Config: {active_cfg} ({REMOTE_CFG_DIR}/{active_cfg})")
    print("=" * 72)

def interactive_loop():
    try:
        ssh = get_ssh()
    except Exception as e:
        print(f"[ERROR] Could not connect to SSH on {SERVER_HOST}: {e}")
        return

    active_cfg, (gt, gm) = detect_active_gamemode(ssh)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header(active_cfg)
        print("  [1] Search Command / Setting (e.g. mp_roundtime, money, freeze)")
        print("  [2] View & Quick-Edit Popular Match Settings")
        print("  [3] Set / Update Any Command Value")
        print("  [4] Execute Live Server Command (RCON)")
        print("  [5] Switch Target Config File (server.cfg, gamemode_*.cfg)")
        print("  [6] Restart CS2 Match / Round (mp_restartgame 1)")
        print("  [7] Restart CS2 Server Service")
        print("  [0] Exit")
        print("-" * 72)

        choice = input("Select an option [0-7]: ").strip()

        if choice == "0":
            print("\nExiting. Goodbye!")
            ssh.close()
            break

        elif choice == "1":
            query = input("\nEnter command name or keyword to search: ").strip()
            if not query: continue
            content = read_cfg(ssh, active_cfg)
            parsed = parse_cfg_lines(content)
            matches = search_in_cfg(parsed, query)

            print(f"\n--- Search results for '{query}' in {active_cfg} ---")
            if not matches:
                print(f"  No matches found in {active_cfg}.")
                live_val = get_live_convar(query)
                print(f"  Live server value for '{query}': {live_val}")
            else:
                for line_idx, item in matches:
                    cmd = item["cmd"]
                    cfg_val = item["val"]
                    comment = item["comment"]
                    live_val = get_live_convar(cmd)
                    print(f"\n  * Command:    {cmd}")
                    print(f"    CFG Value:  {cfg_val}")
                    print(f"    Live Value: {live_val}")
                    if comment:
                        print(f"    Comment:    {comment}")

            input("\nPress Enter to continue...")

        elif choice == "2":
            print(f"\n--- Popular Match Settings ({active_cfg}) ---")
            content = read_cfg(ssh, active_cfg)
            parsed = parse_cfg_lines(content)
            
            for i, (cmd, desc) in enumerate(POPULAR_SETTINGS, 1):
                matches = search_in_cfg(parsed, cmd)
                cfg_val = matches[0][1]["val"] if matches else "(not set in cfg)"
                print(f"  [{i:2d}] {cmd:<24} = {cfg_val:<8} (Live: {get_live_convar(cmd)})")
                print(f"       -> {desc}")

            print("-" * 72)
            sel = input("Enter number [1-16] to edit, or Enter to go back: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(POPULAR_SETTINGS):
                cmd, desc = POPULAR_SETTINGS[int(sel) - 1]
                matches = search_in_cfg(parsed, cmd)
                cur = matches[0][1]["val"] if matches else get_live_convar(cmd)
                new_val = input(f"Enter new value for {cmd} [current: {cur}]: ").strip()
                if new_val:
                    new_content, existed = modify_convar(parsed, cmd, new_val)
                    bak = write_cfg_with_backup(ssh, active_cfg, new_content)
                    print(f"[OK] Saved to {active_cfg}! (Backup: {os.path.basename(bak)})")

                    # Live apply
                    rcon_res = rcon_exec(f"{cmd} {new_val}")
                    print(f"[LIVE] Applied {cmd} {new_val} to running server via RCON!")

                    ask_restart = input("Restart live round to apply immediately? (mp_restartgame 1) [y/N]: ").strip().lower()
                    if ask_restart == 'y':
                        rcon_exec("mp_restartgame 1")
                        print("[LIVE] Executed mp_restartgame 1!")
                    input("\nPress Enter to continue...")

        elif choice == "3":
            cmd = input("\nEnter convar/command name (e.g. mp_roundtime_defuse): ").strip()
            if not cmd: continue
            content = read_cfg(ssh, active_cfg)
            parsed = parse_cfg_lines(content)
            matches = search_in_cfg(parsed, cmd)
            cur = matches[0][1]["val"] if matches else get_live_convar(cmd)
            
            new_val = input(f"Enter new value for '{cmd}' [Current: {cur}]: ").strip()
            if not new_val: continue

            new_content, existed = modify_convar(parsed, cmd, new_val)
            bak = write_cfg_with_backup(ssh, active_cfg, new_content)
            print(f"[OK] Saved to {active_cfg}! (Backup: {os.path.basename(bak)})")

            # Apply live
            rcon_exec(f"{cmd} {new_val}")
            print(f"[LIVE] Applied '{cmd} {new_val}' to running server via RCON!")

            ask_restart = input("Restart live round? (mp_restartgame 1) [y/N]: ").strip().lower()
            if ask_restart == 'y':
                rcon_exec("mp_restartgame 1")
                print("[LIVE] Executed mp_restartgame 1!")

            input("\nPress Enter to continue...")

        elif choice == "4":
            cmd = input("\nEnter console/RCON command to execute on live server (e.g. status, changelevel de_dust2, mp_restartgame 1): ").strip()
            if cmd:
                print(f"[RCON] Executing '{cmd}'...")
                res = rcon_exec(cmd)
                print("-" * 72)
                print(res if res else "[No response or command accepted silently]")
                print("-" * 72)
            input("\nPress Enter to continue...")

        elif choice == "5":
            _, stdout, _ = ssh.exec_command(f"ls {REMOTE_CFG_DIR}/gamemode_*.cfg {REMOTE_CFG_DIR}/server.cfg")
            files = [os.path.basename(f.strip()) for f in stdout.read().decode().splitlines() if f.strip()]
            print("\nAvailable CFG files:")
            for i, f in enumerate(files, 1):
                marker = " (ACTIVE)" if f == active_cfg else ""
                print(f"  [{i}] {f}{marker}")
            fsel = input(f"Select file number [1-{len(files)}] or Enter to keep '{active_cfg}': ").strip()
            if fsel.isdigit() and 1 <= int(fsel) <= len(files):
                active_cfg = files[int(fsel) - 1]
                print(f"[OK] Switched active config to {active_cfg}")
                input("\nPress Enter to continue...")

        elif choice == "6":
            rcon_exec("mp_restartgame 1")
            print("\n[OK] Sent 'mp_restartgame 1' via RCON! Match/Round restarted.")
            input("\nPress Enter to continue...")

        elif choice == "7":
            confirm = input("\nAre you sure you want to restart the full CS2 server service? [y/N]: ").strip().lower()
            if confirm == 'y':
                print("[RESTART] Running systemctl restart cs2...")
                ssh.exec_command("systemctl restart cs2")
                print("[OK] CS2 service restarted.")
            input("\nPress Enter to continue...")

# ================= Command-Line Argument Mode =================
def cli_mode():
    if len(sys.argv) < 2:
        interactive_loop()
        return

    action = sys.argv[1].lower()

    if action in ["--help", "-h", "help"]:
        print("""Usage:
  python cs2_cfg.py                           (Opens interactive menu)
  python cs2_cfg.py search <query>             (Search for any convar in active cfg)
  python cs2_cfg.py get <convar>               (Get convar value from cfg and live server)
  python cs2_cfg.py set <convar> <value>       (Update convar in cfg + apply live to server)
  python cs2_cfg.py rcon <command>             (Run any RCON command on live server)
  python cs2_cfg.py restart                    (Restart live match: mp_restartgame 1)
        """)
        return

    ssh = get_ssh()
    active_cfg, _ = detect_active_gamemode(ssh)

    if action == "search":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a search query. Example: python cs2_cfg.py search mp_roundtime")
            return
        query = sys.argv[2]
        content = read_cfg(ssh, active_cfg)
        parsed = parse_cfg_lines(content)
        matches = search_in_cfg(parsed, query)
        print(f"=== Search results for '{query}' in {active_cfg} ===")
        if not matches:
            print(f"  No match in {active_cfg}. Live server: {get_live_convar(query)}")
        else:
            for _, item in matches:
                cmd = item["cmd"]
                val = item["val"]
                live = get_live_convar(cmd)
                comm = f" // {item['comment']}" if item["comment"] else ""
                print(f"  {cmd:<28} = {val:<8} (Live: {live}){comm}")

    elif action == "get":
        if len(sys.argv) < 3:
            print("[ERROR] Please specify convar. Example: python cs2_cfg.py get mp_roundtime_defuse")
            return
        cmd = sys.argv[2]
        content = read_cfg(ssh, active_cfg)
        parsed = parse_cfg_lines(content)
        matches = search_in_cfg(parsed, cmd)
        cfg_val = matches[0][1]["val"] if matches else "(not found in cfg)"
        live_val = get_live_convar(cmd)
        print(f"Convar:     {cmd}")
        print(f"In CFG:     {cfg_val}")
        print(f"On Server:  {live_val}")

    elif action == "set":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: python cs2_cfg.py set <convar> <new_value>")
            print("Example: python cs2_cfg.py set mp_roundtime_defuse 2")
            return
        cmd = sys.argv[2]
        val = sys.argv[3]
        content = read_cfg(ssh, active_cfg)
        parsed = parse_cfg_lines(content)
        new_content, existed = modify_convar(parsed, cmd, val)
        bak = write_cfg_with_backup(ssh, active_cfg, new_content)
        print(f"[OK] Saved {cmd} = {val} in {active_cfg} (Backup: {os.path.basename(bak)})")
        
        # Apply live
        rcon_exec(f"{cmd} {val}")
        print(f"[LIVE] Applied '{cmd} {val}' via RCON!")
        
        # Check if match restart flag given
        if "--restart" in sys.argv:
            rcon_exec("mp_restartgame 1")
            print("[LIVE] Executed mp_restartgame 1!")

    elif action == "rcon":
        cmd = " ".join(sys.argv[2:])
        if not cmd:
            print("[ERROR] Please provide RCON command.")
            return
        res = rcon_exec(cmd)
        print(res if res else "[Executed]")

    elif action == "restart":
        rcon_exec("mp_restartgame 1")
        print("[OK] Match restarted via mp_restartgame 1")

    else:
        print(f"[ERROR] Unknown action '{action}'. Run with --help for usage.")

    ssh.close()

if __name__ == "__main__":
    cli_mode()
