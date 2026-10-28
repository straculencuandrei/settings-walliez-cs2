#!/usr/bin/env python3
"""
CS2 Unified Server Control Center
=================================
Modern, ultra-fast web-based desktop application for managing all CS2 server
features, announcements, convars, server title, Discord bot, and MVP anthems.
"""

import os
import re
import sys
import json
import time
import socket
import struct
import shutil
import base64
import urllib.request
import subprocess
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import paramiko

# Configuration
SERVER_HOST = "81.181.113.120"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = ")(e092e8EjTUiV"
RCON_PORT = 27015
RCON_PASS = "walliez_rcon_2026"

REMOTE_ANNOUNCER_PATH = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/ServerAnnouncer/ServerAnnouncer.json"
REMOTE_SERVER_CFG = "/home/csgoserver/server-cs2/game/csgo/cfg/server.cfg"
REMOTE_COMP_CFG = "/home/csgoserver/server-cs2/game/csgo/cfg/gamemode_competitive_server.cfg"
REMOTE_CHATMANAGER_CONFIG = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/ChatManager/ChatManager.json"
REMOTE_ADMINS_CONFIG = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/admins.json"
REMOTE_ADMIN_GROUPS_CONFIG = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/admin_groups.json"

FFMPEG_CANDIDATES = [
    r"C:\Users\buzunar\Documents\game\ytallinone\bin\ffmpeg.exe",
    shutil.which("ffmpeg") or ""
]

def find_ffmpeg():
    for p in FFMPEG_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None

def get_ssh_client(timeout=8):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=timeout)
    return ssh

def rcon_exec(command, timeout=3.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((SERVER_HOST, RCON_PORT))
        auth = struct.pack('<iii', len(RCON_PASS) + 10, 1, 3) + RCON_PASS.encode('ascii') + b'\x00\x00'
        s.send(auth)
        s.recv(4096)
        exec_pkt = struct.pack('<iii', len(command) + 10, 2, 2) + command.encode('ascii') + b'\x00\x00'
        s.send(exec_pkt)
        out = s.recv(4096)
        s.close()
        return out[12:].decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"RCON Error: {e}"

def get_tags_and_staff_payload():
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_CHATMANAGER_CONFIG, 'r') as f:
        cm_data = json.loads(f.read().decode('utf-8'))
    with sftp.open(REMOTE_ADMINS_CONFIG, 'r') as f:
        raw_admins = f.read().decode('utf-8').lstrip('\ufeff')
        admins_data = json.loads(raw_admins)
    with sftp.open(REMOTE_ADMIN_GROUPS_CONFIG, 'r') as f:
        raw_groups = f.read().decode('utf-8').lstrip('\ufeff')
        groups_data = json.loads(raw_groups)
    sftp.close()
    ssh.close()

    tags = cm_data.get("Tags", {})
    staff_by_id = {}
    for entry_key, entry in admins_data.items():
        ident = str(entry.get("identity", entry_key)).strip()
        if not ident:
            continue
        name = entry.get("name", entry_key)
        groups = entry.get("groups", [])
        if ident not in staff_by_id:
            staff_by_id[ident] = {
                "identity": ident,
                "names": set(),
                "groups": [],
                "immunity": entry.get("immunity", 0),
                "flags": entry.get("flags", [])
            }
        if name:
            staff_by_id[ident]["names"].add(name)
        if entry_key != ident:
            staff_by_id[ident]["names"].add(entry_key)
        for g in groups:
            if g not in staff_by_id[ident]["groups"]:
                staff_by_id[ident]["groups"].append(g)

    staff_list = []
    for ident, info in staff_by_id.items():
        display_name = " / ".join(sorted(info["names"])) or ident
        matching_tag_groups = [g for g in info["groups"] if g in tags]
        has_steam_tag = ident in tags
        has_overlap = (len(matching_tag_groups) > 1) or (has_steam_tag and len(matching_tag_groups) > 0)

        if has_steam_tag:
            active_tag_key = ident
        elif matching_tag_groups:
            active_tag_key = matching_tag_groups[0]
        elif info["groups"]:
            active_tag_key = info["groups"][0]
        else:
            active_tag_key = "Default"

        staff_list.append({
            "identity": ident,
            "name": display_name,
            "groups": info["groups"],
            "matching_tag_groups": matching_tag_groups,
            "has_overlap": has_overlap,
            "active_tag_key": active_tag_key,
            "has_steam_tag": has_steam_tag,
            "immunity": info["immunity"]
        })

    return {
        "success": True,
        "tags": tags,
        "staff": staff_list,
        "groups": list(groups_data.keys()),
        "team_tags": cm_data.get("TeamTags", {})
    }

def a2s_info():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        query = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(query, (SERVER_HOST, RCON_PORT))
        resp, _ = sock.recvfrom(4096)
        if resp.startswith(b'\xFF\xFF\xFF\xFF\x41'):
            challenge = resp[5:9]
            sock.sendto(query + challenge, (SERVER_HOST, RCON_PORT))
            resp, _ = sock.recvfrom(4096)
        sock.close()
        if len(resp) >= 6 and resp[4:5] == b'I':
            idx = 5
            protocol = resp[idx]
            idx += 1
            end = resp.find(b'\x00', idx)
            name = resp[idx:end].decode('utf-8', errors='replace')
            idx = end + 1
            end = resp.find(b'\x00', idx)
            map_name = resp[idx:end].decode('utf-8', errors='replace')
            idx = end + 1
            end = resp.find(b'\x00', idx) # folder
            idx = end + 1
            end = resp.find(b'\x00', idx) # game
            idx = end + 1 + 2 # skip appid
            players = resp[idx]
            max_players = resp[idx+1]
            return {"online": True, "name": name, "map": map_name, "players": players, "max_players": max_players}
    except Exception:
        pass
    return {"online": False, "name": "Counter-Strike 2 Server", "map": "Unknown", "players": 0, "max_players": 24}

# Workshop & MVP Constants
WORKSHOP_ID = "3827657422"
ADDON_NAME = "wlzMVP"
ADDON_TITLE = "wlzMVP"
ADDON_AUTHOR = "Walliez"
ADDON_DESC = "wlzMVP - Custom Server MVP Music Pack"

CS2_ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive"
LOCAL_BACKUP = r"C:\Users\buzunar\Documents\cs2server\wlzMVP"
CONTENT_DIR = os.path.join(CS2_ROOT, "content", "csgo_addons", ADDON_NAME)
GAME_DIR = os.path.join(CS2_ROOT, "game", "csgo_addons", ADDON_NAME)
VPK_DIR = os.path.join(CS2_ROOT, "game", "csgo_addons", "vpks", WORKSHOP_ID)
COMPILER_EXE = os.path.join(CS2_ROOT, "game", "bin", "win64", "resourcecompiler.exe")
CS2_EXE = os.path.join(CS2_ROOT, "game", "bin", "win64", "cs2.exe")

REMOTE_MVP_SETTINGS = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json"
REMOTE_WORKSHOP_PATHS = [
    f"/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/{WORKSHOP_ID}",
    f"/home/csgoserver/server-cs2/steamapps/workshop/content/730/{WORKSHOP_ID}",
    f"/home/csgoserver/Steam/steamapps/workshop/content/730/{WORKSHOP_ID}"
]

def sanitize_id(text):
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', text.strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean.lower() or "custom_mvp"

def format_start_time(st):
    st = str(st).strip()
    if not st:
        return "00:00:00"
    if ":" in st:
        parts = st.split(":")
        if len(parts) == 2:
            return f"00:{int(parts[0]):02d}:{int(parts[1]):02d}"
        if len(parts) == 3:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
    try:
        secs = int(float(st))
        mins = int(secs // 60)
        rem_secs = int(secs % 60)
        return f"00:{mins:02d}:{rem_secs:02d}"
    except ValueError:
        return "00:00:00"

def browse_audio_files(multiple=True):
    # Method 1: Detached python process with dedicated Tkinter main loop (prevents COM/thread apartment deadlocks)
    try:
        sub_code = (
            "import tkinter as tk, os\n"
            "from tkinter import filedialog\n"
            "r = tk.Tk()\n"
            "r.withdraw()\n"
            "r.attributes('-topmost', True)\n"
            f"paths = filedialog.askopenfilenames(title='Select Audio File(s) for MVP Anthems', filetypes=[('Audio Files', '*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma'), ('All Files', '*.*')]) if {multiple} else [filedialog.askopenfilename(title='Select Audio File for MVP Anthem', filetypes=[('Audio Files', '*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma'), ('All Files', '*.*')])]\n"
            "r.destroy()\n"
            "for p in paths:\n"
            "    if p and p.strip(): print(os.path.normpath(p.strip()))\n"
        )
        res = subprocess.run([sys.executable, "-c", sub_code], capture_output=True, text=True, timeout=120)
        if res.returncode == 0 and res.stdout.strip():
            lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
            return lines if multiple else lines[:1]
    except Exception as e:
        print(f"[!] Detached file dialog error: {e}")

    # Method 2: Direct Tkinter fallback
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        if multiple:
            paths = filedialog.askopenfilenames(
                title="Select Audio File(s) for MVP Anthems",
                filetypes=[
                    ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma"),
                    ("All Files", "*.*")
                ]
            )
            root.destroy()
            return [os.path.normpath(p) for p in paths if p] if paths else []
        else:
            path = filedialog.askopenfilename(
                title="Select Audio File for MVP Anthem",
                filetypes=[
                    ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma"),
                    ("All Files", "*.*")
                ]
            )
            root.destroy()
            return [os.path.normpath(path)] if path else []
    except Exception as e:
        print(f"[!] Tkinter fallback error: {e}")
        return []

def browse_audio_file():
    paths = browse_audio_files(multiple=False)
    return paths[0] if paths else ""

def execute_mvp_batch_pipeline(tracks):
    import tempfile
    import vpk

    if not tracks:
        yield {"step": 1, "status": "failed", "msg": "No audio tracks provided in batch queue."}
        return

    valid_tracks = []
    for tr in tracks:
        p = tr.get("audio_path", "").strip(' "\'')
        if p and os.path.exists(p):
            cid = sanitize_id(tr.get("clean_id", "") or os.path.splitext(os.path.basename(p))[0])
            name = tr.get("display_name", "").strip() or os.path.splitext(os.path.basename(p))[0].replace("_", " ").title()
            start = format_start_time(tr.get("start_time", "00:00:00"))
            try:
                dur = float(tr.get("duration", 10.0))
                dur = max(3.0, min(25.0, dur))
            except (ValueError, TypeError):
                dur = 10.0
            valid_tracks.append({
                "audio_path": p,
                "display_name": name,
                "start_time": start,
                "duration": dur,
                "clean_id": cid
            })

    if not valid_tracks:
        yield {"step": 1, "status": "failed", "msg": "Specified audio file(s) do not exist on disk."}
        return

    for d in [
        os.path.join(CONTENT_DIR, "sounds", "mvp"),
        os.path.join(CONTENT_DIR, "soundevents"),
        os.path.join(GAME_DIR, "sounds", "mvp"),
        os.path.join(GAME_DIR, "soundevents"),
        os.path.join(LOCAL_BACKUP, "sounds", "mvp"),
        os.path.join(LOCAL_BACKUP, "soundevents"),
        VPK_DIR
    ]:
        os.makedirs(d, exist_ok=True)

    ffmpeg_local = find_ffmpeg()
    total_tracks = len(valid_tracks)

    # STEP 1: Trim & Master All Audio Tracks
    yield {"step": 1, "status": "running", "msg": f"Mastering {total_tracks} track(s) (PCM WAV, 44.1kHz, customized duration)..."}

    for i, t in enumerate(valid_tracks, start=1):
        cid = t["clean_id"]
        fmt_start = t["start_time"]
        dur = t["duration"]
        fade_start = max(0.0, dur - 1.0)
        p = t["audio_path"]
        name = t["display_name"]

        dest_wav = os.path.join(CONTENT_DIR, "sounds", "mvp", f"{cid}.wav")
        backup_wav = os.path.join(LOCAL_BACKUP, "sounds", "mvp", f"{cid}.wav")
        converted_ok = False

        if ffmpeg_local and os.path.exists(ffmpeg_local):
            try:
                cmd = [
                    ffmpeg_local, "-y", "-ss", fmt_start, "-i", p,
                    "-t", str(dur), "-af", f"afade=t=out:st={fade_start:.1f}:d=1",
                    "-c:a", "pcm_s16le", "-ar", "44100", dest_wav
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                shutil.copy2(dest_wav, backup_wav)
                converted_ok = True
            except Exception:
                converted_ok = False

        if not converted_ok:
            try:
                ssh = get_ssh_client(timeout=20)
                sftp = ssh.open_sftp()
                rem_in = f"/tmp/mvp_in_{cid}.tmp"
                rem_wav = f"/tmp/mvp_out_{cid}.wav"
                sftp.put(p, rem_in)
                cmd = f"/usr/local/bin/ffmpeg -y -ss {fmt_start} -i {rem_in} -t {dur} -af 'afade=t=out:st={fade_start:.1f}:d=1' -c:a pcm_s16le -ar 44100 {rem_wav}"
                _, stdout, _ = ssh.exec_command(cmd)
                stdout.channel.recv_exit_status()
                sftp.get(rem_wav, dest_wav)
                sftp.close()
                ssh.exec_command(f"rm -f {rem_in} {rem_wav}")
                ssh.close()
                shutil.copy2(dest_wav, backup_wav)
                converted_ok = True
            except Exception as e:
                yield {"step": 1, "status": "failed", "msg": f"Failed mastering '{name}': {e}"}
                return

        yield {"step": 1, "status": "running", "msg": f"[{i}/{total_tracks}] Mastered '{name}' ({dur:.1f}s from {fmt_start})"}

    yield {"step": 1, "status": "completed", "msg": f"All {total_tracks} track(s) mastered into 44.1kHz PCM WAV"}

    # STEP 2: Generate / Update KV3 soundevents_addon.vsndevts
    yield {"step": 2, "status": "running", "msg": "Generating KV3 soundevents definitions for all anthems..."}
    try:
        local_mvp_dir = os.path.join(LOCAL_BACKUP, "sounds", "mvp")
        all_tracks = []
        if os.path.exists(local_mvp_dir):
            for f in os.listdir(local_mvp_dir):
                if f.lower().endswith(".wav"):
                    k = sanitize_id(os.path.splitext(f)[0])
                    if k not in all_tracks:
                        all_tracks.append(k)
        for t in valid_tracks:
            if t["clean_id"] not in all_tracks:
                all_tracks.append(t["clean_id"])

        soundevents_lines = [
            "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->",
            "{"
        ]
        for tid in all_tracks:
            soundevents_lines.append(f'    "CustomMVP.{tid}" =')
            soundevents_lines.append("    {")
            soundevents_lines.append('        type = "csgo_mega"')
            soundevents_lines.append("        volume = 1.000000")
            soundevents_lines.append("        pitch = 1.000000")
            soundevents_lines.append(f'        vsnd_files_track_01 = "sounds/mvp/{tid}.vsnd"')
            soundevents_lines.append("    }")
        soundevents_lines.append("}")
        vsndevts_content = "\n".join(soundevents_lines) + "\n"

        for target in [
            os.path.join(CONTENT_DIR, "soundevents", "soundevents_addon.vsndevts"),
            os.path.join(CONTENT_DIR, "soundevents_addon.vsndevts"),
            os.path.join(LOCAL_BACKUP, "soundevents", "soundevents_addon.vsndevts"),
            os.path.join(LOCAL_BACKUP, "soundevents_addon.vsndevts")
        ]:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(vsndevts_content)

        addoninfo_text = f'''"AddonInfo"
{{
    "addonTitle"         "{ADDON_TITLE}"
    "addonVersion"       "1.0"
    "addonAuthor"        "{ADDON_AUTHOR}"
    "addonDescription"   "{ADDON_DESC}"
    "addonSteamAppID"    "730"
}}
'''
        for target in [
            os.path.join(CONTENT_DIR, "addoninfo.txt"),
            os.path.join(GAME_DIR, "addoninfo.txt"),
            os.path.join(LOCAL_BACKUP, "addoninfo.txt")
        ]:
            with open(target, "w", encoding="utf-8") as f:
                f.write(addoninfo_text)

        yield {"step": 2, "status": "completed", "msg": f"KV3 definitions updated ({len(all_tracks)} total tracks in addon)"}
    except Exception as e:
        yield {"step": 2, "status": "failed", "msg": f"Soundevents generation failed: {e}"}
        return

    # STEP 3: Compile Source 2 Assets with resourcecompiler.exe
    yield {"step": 3, "status": "running", "msg": "Compiling binary .vsnd_c and .vsndevts_c assets..."}
    try:
        cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        compiled_count = 0
        for t in valid_tracks:
            vsnd_path = os.path.join(GAME_DIR, "sounds", "mvp", f"{t['clean_id']}.vsnd_c")
            if os.path.exists(vsnd_path):
                compiled_count += 1
        yield {"step": 3, "status": "completed", "msg": f"Resource compiler successfully built assets ({compiled_count}/{total_tracks} verified)"}
    except Exception as e:
        yield {"step": 3, "status": "failed", "msg": f"Resource compilation failed: {e}"}
        return

    # STEP 4: Register all tracks in Server MVP_Settings.json & Local Backup
    yield {"step": 4, "status": "running", "msg": f"Registering {total_tracks} anthem(s) in server database..."}
    try:
        ssh = get_ssh_client(timeout=15)
        sftp = ssh.open_sftp()
        server_mvp_data = {}
        try:
            with sftp.open(REMOTE_MVP_SETTINGS, "r") as f:
                server_mvp_data = json.loads(f.read().decode('utf-8'))
        except Exception:
            server_mvp_data = {}

        for t in valid_tracks:
            cid = t["clean_id"]
            name = t["display_name"]
            dur = int(round(t["duration"]))
            kit_id = f"mvp_{cid}"
            server_mvp_data[kit_id] = {
                "MVP_Kit_Name": name,
                "Sound_Path_1": f"sounds/mvp/{cid}.vsnd_c",
                "SoundEvent": f"CustomMVP.{cid}",
                "Sound_Event": f"CustomMVP.{cid}",
                "CanBePreview": True,
                "Message_Chat": True,
                "Message_Center_Bottom": True,
                "Message_Center_Bottom_InSecs": dur
            }

        formatted_json = json.dumps(server_mvp_data, indent=2, ensure_ascii=False)
        with sftp.open(REMOTE_MVP_SETTINGS, "w") as f:
            f.write(formatted_json)
        sftp.close()
        ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
        ssh.close()

        with open(os.path.join(LOCAL_BACKUP, "MVP_Settings.json"), "w", encoding="utf-8") as f:
            f.write(formatted_json)

        yield {"step": 4, "status": "completed", "msg": f"Registered {total_tracks} anthem(s) in server MVP_Settings.json with custom durations"}
    except Exception as e:
        yield {"step": 4, "status": "failed", "msg": f"Failed updating server settings: {e}"}
        return

    # STEP 5: Pack & Deploy Workshop VPK Cache
    yield {"step": 5, "status": "running", "msg": "Packaging Valve VPK and deploying to server workshop cache..."}
    try:
        staging = tempfile.mkdtemp()
        os.makedirs(os.path.join(staging, "sounds", "mvp"), exist_ok=True)
        os.makedirs(os.path.join(staging, "soundevents"), exist_ok=True)

        game_mvp_dir = os.path.join(GAME_DIR, "sounds", "mvp")
        if os.path.exists(game_mvp_dir):
            for f in os.listdir(game_mvp_dir):
                if f.endswith(".vsnd_c"):
                    shutil.copyfile(os.path.join(game_mvp_dir, f), os.path.join(staging, "sounds", "mvp", f))

        se_c = os.path.join(GAME_DIR, "soundevents_addon.vsndevts_c")
        if os.path.exists(se_c):
            shutil.copyfile(se_c, os.path.join(staging, "soundevents_addon.vsndevts_c"))
            shutil.copyfile(se_c, os.path.join(staging, "soundevents", "soundevents_addon.vsndevts_c"))

        addoninfo_src = os.path.join(GAME_DIR, "addoninfo.txt")
        if os.path.exists(addoninfo_src):
            shutil.copyfile(addoninfo_src, os.path.join(staging, "addoninfo.txt"))

        temp_vpk = os.path.join(tempfile.gettempdir(), f"{WORKSHOP_ID}.vpk")
        pak = vpk.new(staging)
        pak.save(temp_vpk)
        shutil.rmtree(staging)
        vpk_size = os.path.getsize(temp_vpk)

        now_ts = int(time.time())
        now_readable = time.strftime("%m/%d/%Y %I:%M:%S %p")
        publish_data_content = f'''"publish_data"
{{
\t"title"\t\t"{ADDON_TITLE}"
\t"source_folder"\t\t"{ADDON_NAME}"
\t"publish_time"\t\t"{now_ts}"
\t"publish_time_readable"\t\t"{now_readable}"
}}
'''
        os.makedirs(VPK_DIR, exist_ok=True)
        with open(os.path.join(VPK_DIR, "publish_data.txt"), "w", encoding="utf-8") as f:
            f.write(publish_data_content)
        shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}.vpk"))

        ssh = get_ssh_client(timeout=20)
        sftp = ssh.open_sftp()
        for rem_dir in REMOTE_WORKSHOP_PATHS:
            ssh.exec_command(f"mkdir -p {rem_dir}")
            sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
            sftp.put(os.path.join(VPK_DIR, "publish_data.txt"), f"{rem_dir}/publish_data.txt")
        sftp.close()

        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")

        # Deploy standalone MP3 / VSND_C for Web Preview & Direct Server Fallback
        remote_sound_dirs = [
            "/home/csgoserver/server-cs2/game/csgo/sounds/mvp",
            "/home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/sounds/mvp"
        ]
        ffmpeg_local = find_ffmpeg()
        sftp = ssh.open_sftp()
        for t in valid_tracks:
            cid = t["clean_id"]
            wav_src = os.path.join(CONTENT_DIR, "sounds", "mvp", f"{cid}.wav")
            vsnd_src = os.path.join(GAME_DIR, "sounds", "mvp", f"{cid}.vsnd_c")
            mp3_temp = os.path.join(tempfile.gettempdir(), f"{cid}.mp3")

            # Generate MP3 for web streaming
            if os.path.exists(wav_src):
                if ffmpeg_local and os.path.exists(ffmpeg_local):
                    try:
                        subprocess.run([ffmpeg_local, "-y", "-i", wav_src, "-b:a", "320k", mp3_temp], capture_output=True, check=True)
                    except Exception:
                        pass

            for snd_dir in remote_sound_dirs:
                ssh.exec_command(f"mkdir -p {snd_dir}")
                if os.path.exists(mp3_temp):
                    sftp.put(mp3_temp, f"{snd_dir}/{cid}.mp3")
                if os.path.exists(vsnd_src):
                    sftp.put(vsnd_src, f"{snd_dir}/{cid}.vsnd_c")
                if os.path.exists(wav_src):
                    sftp.put(wav_src, f"{snd_dir}/{cid}.wav")

            if os.path.exists(mp3_temp):
                os.remove(mp3_temp)

        sftp.close()
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/sounds/mvp")
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/sounds/mvp")
        ssh.exec_command("chmod -R 755 /home/csgoserver/server-cs2/game/csgo/sounds/mvp")
        ssh.exec_command("chmod -R 755 /home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/sounds/mvp")
        ssh.close()
        os.remove(temp_vpk)

        yield {"step": 5, "status": "completed", "msg": f"VPK deployed: {vpk_size:,} bytes across all server paths"}
    except Exception as e:
        yield {"step": 5, "status": "failed", "msg": f"VPK build/deploy failed: {e}"}
        return

    # STEP 6: Synchronize Local CS2 Game Files
    yield {"step": 6, "status": "running", "msg": "Synchronizing local Counter-Strike 2 game files..."}
    try:
        steam_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"E:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo"
        ]
        local_cs2 = next((p for p in steam_paths if os.path.exists(p)), None)
        if local_cs2:
            target_sound_dir = os.path.join(local_cs2, "sounds", "mvp")
            os.makedirs(target_sound_dir, exist_ok=True)
            for t in valid_tracks:
                compiled_src = os.path.join(GAME_DIR, "sounds", "mvp", f"{t['clean_id']}.vsnd_c")
                if os.path.exists(compiled_src):
                    shutil.copy2(compiled_src, os.path.join(target_sound_dir, f"{t['clean_id']}.vsnd_c"))
        yield {"step": 6, "status": "completed", "msg": f"Synchronized {total_tracks} anthem(s) to local CS2 files"}
    except Exception as e:
        yield {"step": 6, "status": "completed", "msg": f"Local sync notice: {e}"}

    # STEP 7: Finished - Ready to Update in Workshop Pack
    yield {
        "step": 7,
        "status": "completed",
        "msg": f"Successfully mastered & deployed {total_tracks} anthem(s)! Workshop pack wlzMVP is fully compiled and ready to update."
    }

def execute_mvp_pipeline(audio_path, display_name, start_time="00:00:00", duration=10.0):
    return execute_mvp_batch_pipeline([{
        "audio_path": audio_path,
        "display_name": display_name,
        "start_time": start_time,
        "duration": duration
    }])

def sync_local_client_files():
    steam_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
        r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
        r"E:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo"
    ]
    local_cs2 = next((p for p in steam_paths if os.path.exists(p)), None)
    if not local_cs2:
        return "Could not locate local CS2 directory in Steam libraries."
    dest_dir = os.path.join(local_cs2, "sounds", "mvp")
    os.makedirs(dest_dir, exist_ok=True)
    src_dir = os.path.join(GAME_DIR, "sounds", "mvp")
    copied = 0
    if os.path.exists(src_dir):
        for f in os.listdir(src_dir):
            if f.endswith(".vsnd_c"):
                shutil.copy2(os.path.join(src_dir, f), os.path.join(dest_dir, f))
                copied += 1
    return f"Synced {copied} anthem(s) directly to local CS2: {dest_dir}"

def convert_audio_clean_mp3(input_file):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise FileNotFoundError("Local ffmpeg.exe could not be found.")
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}_clean_44k.mp3"
    cmd = [
        ffmpeg, "-y", "-i", input_file,
        "-t", "10", "-af", "afade=t=out:st=9:d=1",
        "-codec:a", "libmp3lame", "-b:a", "320k",
        "-ar", "44100", "-ac", "2",
        "-map_metadata", "-1", "-id3v2_version", "3",
        output_file
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    return f"Created clean 44.1kHz MP3: {output_file} ({os.path.getsize(output_file):,} bytes)"

def rebuild_full_workshop_addon():
    import tempfile
    import vpk
    # 1. Compile resources
    cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    # 2. Package VPK
    staging = tempfile.mkdtemp()
    os.makedirs(os.path.join(staging, "sounds", "mvp"), exist_ok=True)
    os.makedirs(os.path.join(staging, "soundevents"), exist_ok=True)

    game_mvp_dir = os.path.join(GAME_DIR, "sounds", "mvp")
    if os.path.exists(game_mvp_dir):
        for f in os.listdir(game_mvp_dir):
            if f.endswith(".vsnd_c"):
                shutil.copyfile(os.path.join(game_mvp_dir, f), os.path.join(staging, "sounds", "mvp", f))

    se_c = os.path.join(GAME_DIR, "soundevents_addon.vsndevts_c")
    if os.path.exists(se_c):
        shutil.copyfile(se_c, os.path.join(staging, "soundevents_addon.vsndevts_c"))
        shutil.copyfile(se_c, os.path.join(staging, "soundevents", "soundevents_addon.vsndevts_c"))

    addoninfo_src = os.path.join(GAME_DIR, "addoninfo.txt")
    if os.path.exists(addoninfo_src):
        shutil.copyfile(addoninfo_src, os.path.join(staging, "addoninfo.txt"))

    temp_vpk = os.path.join(tempfile.gettempdir(), f"{WORKSHOP_ID}.vpk")
    pak = vpk.new(staging)
    pak.save(temp_vpk)
    shutil.rmtree(staging)
    vpk_size = os.path.getsize(temp_vpk)

    now_ts = int(time.time())
    now_readable = time.strftime("%m/%d/%Y %I:%M:%S %p")
    publish_data_content = f'''"publish_data"
{{
\t"title"\t\t"{ADDON_TITLE}"
\t"source_folder"\t\t"{ADDON_NAME}"
\t"publish_time"\t\t"{now_ts}"
\t"publish_time_readable"\t\t"{now_readable}"
}}
'''
    os.makedirs(VPK_DIR, exist_ok=True)
    with open(os.path.join(VPK_DIR, "publish_data.txt"), "w", encoding="utf-8") as f:
        f.write(publish_data_content)
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}.vpk"))

    ssh = get_ssh_client(timeout=15)
    sftp = ssh.open_sftp()
    for rem_dir in REMOTE_WORKSHOP_PATHS:
        ssh.exec_command(f"mkdir -p {rem_dir}")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
        sftp.put(os.path.join(VPK_DIR, "publish_data.txt"), f"{rem_dir}/publish_data.txt")
    sftp.close()

    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")
    ssh.close()
    os.remove(temp_vpk)
    return f"Rebuilt and deployed workshop addon wlzMVP ({vpk_size:,} bytes) to server cache."

# HTML Template with Pitch-Black Minimalist Luxury UI (Zero Emojis)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS2 Server Control Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #000000;
      --card-bg: #080808;
      --card-border: #1a1a1a;
      --card-border-subtle: #121212;
      --primary: #ffffff;
      --primary-hover: #e4e4e7;
      --accent: #27272a;
      --success: #22c55e;
      --warning: #eab308;
      --danger: #ef4444;
      --text: #ededed;
      --text-muted: #71717a;
      --text-dim: #52525b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Header */
    header {
      background: #000000;
      border-bottom: 1px solid var(--card-border);
      padding: 0 24px;
      height: 54px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 28px;
      height: 28px;
      background: #111111;
      border: 1px solid #27272a;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: #ffffff;
    }
    .brand-title {
      font-size: 0.92rem;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: #ffffff;
    }
    .brand-sub {
      font-size: 0.7rem;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }
    .status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #09090b;
      border: 1px solid var(--card-border);
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 500;
      color: #a1a1aa;
      font-family: 'JetBrains Mono', monospace;
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px rgba(34, 197, 94, 0.7);
    }

    /* App Container & Navigation */
    .app-container {
      max-width: 1100px;
      margin: 0 auto;
      width: 100%;
      padding: 20px 24px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .nav-tabs {
      display: flex;
      gap: 4px;
      background: #080808;
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 500;
      letter-spacing: 0.02em;
      padding: 0 14px;
      height: 32px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text);
      background: #111111;
    }
    .tab-btn.active {
      color: #ffffff;
      background: #141414;
      border-color: #27272a;
      font-weight: 600;
    }

    /* Tab Content Cards */
    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(2px); } to { opacity: 1; transform: translateY(0); } }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 14px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--card-border-subtle);
      flex-wrap: wrap;
    }
    .card-title {
      font-size: 0.92rem;
      font-weight: 600;
      color: #ffffff;
      letter-spacing: -0.01em;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .card-desc {
      font-size: 0.76rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Form Fields */
    .form-group {
      margin-bottom: 14px;
    }
    label {
      display: block;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }
    input[type="text"], input[type="number"], select {
      width: 100%;
      background: #030303;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 0 12px;
      height: 34px;
      color: #f4f4f5;
      font-family: inherit;
      font-size: 0.82rem;
      outline: none;
      transition: border-color 0.15s;
    }
    input[type="text"]:focus, input[type="number"]:focus, select:focus {
      border-color: #3f3f46;
    }
    .input-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-bottom: 14px;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      border-radius: 5px;
      padding: 0 14px;
      height: 32px;
      font-weight: 600;
      font-size: 0.78rem;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
      flex-shrink: 0;
      text-decoration: none;
    }
    .btn:hover {
      background: #e4e4e7;
      border-color: #e4e4e7;
    }
    .btn-secondary {
      background: #111111;
      color: #d4d4d8;
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover {
      background: #18181b;
      color: #ffffff;
      border-color: #3f3f46;
    }
    .btn-danger {
      background: rgba(239, 68, 68, 0.08);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.25);
    }
    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.2);
      color: #ffffff;
      border-color: #ef4444;
    }
    .btn-sm {
      height: 26px;
      padding: 0 10px;
      font-size: 0.72rem;
      border-radius: 4px;
    }

    /* Message Item Rows */
    .msg-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 18px;
    }
    .msg-item {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .msg-text-box {
      flex: 1 1 auto;
      min-width: 0;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: #e4e4e7;
      word-break: break-word;
    }
    .msg-actions {
      flex-shrink: 0;
      display: flex;
      gap: 6px;
    }

    /* CS2 In-Game Chat Simulator */
    .cs2-chat-sim {
      background: #000000;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 14px;
      font-family: 'Segoe UI', Tahoma, sans-serif;
      font-size: 0.88rem;
      min-height: 48px;
      display: flex;
      align-items: center;
      margin-top: 8px;
    }
    .cs2-chat-label {
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-top: 14px;
      margin-bottom: 4px;
    }
    .cs2-preview-text {
      color: #ffffff;
      line-height: 1.4;
      font-weight: 500;
    }

    /* Color Palette Pills */
    .color-tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .color-tag-pill {
      font-size: 0.7rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 0 7px;
      height: 22px;
      line-height: 20px;
      border-radius: 4px;
      background: #0d0d0d;
      cursor: pointer;
      border: 1px solid var(--card-border);
      transition: background 0.15s, border-color 0.15s;
    }
    .color-tag-pill:hover {
      background: #18181b;
      border-color: #3f3f46;
    }

    /* Convars Dense Settings Grid */
    .convars-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 8px;
    }
    .convar-row {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .convar-meta {
      flex: 1 1 auto;
      min-width: 0;
    }
    .convar-name {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 600;
      color: #ffffff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .convar-desc {
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .convar-input {
      width: 76px !important;
      height: 28px !important;
      padding: 0 8px !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.78rem !important;
      text-align: right;
      flex-shrink: 0;
      background: #000000 !important;
      border: 1px solid var(--card-border) !important;
      border-radius: 4px !important;
      color: #ffffff !important;
    }

    /* Action Rows for MVP Studio & FastDL */
    .action-rows-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .action-row {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .action-row-meta {
      flex: 1 1 280px;
    }
    .action-row-title {
      font-size: 0.84rem;
      font-weight: 600;
      color: #ffffff;
    }
    .action-row-desc {
      font-size: 0.74rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Services Grid */
    .services-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .service-card {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
    }
    .service-card .btn {
      width: 100%;
      height: 30px;
    }

    /* Summary Stat Cards */
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .summary-card {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 14px;
    }
    .summary-label {
      font-size: 0.7rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }
    .summary-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      font-weight: 600;
      color: #ffffff;
      margin-top: 4px;
      word-break: break-all;
    }

    /* Terminal Output Drawer */
    .terminal-drawer {
      background: #000000;
      border: 1px solid #18181b;
      border-radius: 4px;
      padding: 10px 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.74rem;
      line-height: 1.5;
      max-height: 120px;
      overflow-y: auto;
      color: #a1a1aa;
      white-space: pre-wrap;
    }

    /* In-App Modal Dialogs */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.82);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
    }
    .modal-overlay.active {
      display: flex;
      animation: modalFade 0.15s ease-out;
    }
    @keyframes modalFade {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .modal-card {
      background: #09090b;
      border: 1px solid #27272a;
      border-radius: 8px;
      width: 100%;
      max-width: 520px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.9);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: modalZoom 0.15s ease-out;
    }
    @keyframes modalZoom {
      from { transform: scale(0.97); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
    .modal-header {
      padding: 12px 16px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #0c0c0e;
    }
    .modal-title {
      font-size: 0.82rem;
      font-weight: 600;
      color: #ffffff;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .modal-close-btn {
      background: transparent;
      border: none;
      color: #71717a;
      font-size: 1.15rem;
      cursor: pointer;
      line-height: 1;
      padding: 2px 6px;
    }
    .modal-close-btn:hover { color: #ffffff; }
    .modal-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    textarea {
      width: 100%;
      background: #030303;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 12px;
      color: #f4f4f5;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      outline: none;
      transition: border-color 0.15s;
      resize: vertical;
    }
    textarea:focus { border-color: #3f3f46; }
    .modal-footer {
      padding: 10px 16px;
      border-top: 1px solid var(--card-border);
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      background: #060608;
    }

    /* Toast Notifications */
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 2000;
      display: flex;
      flex-direction: column;
      gap: 8px;
      pointer-events: none;
    }
    .toast {
      background: #0c0c0e;
      border: 1px solid #27272a;
      border-radius: 6px;
      padding: 10px 14px;
      font-size: 0.78rem;
      color: #ffffff;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      gap: 10px;
      pointer-events: auto;
      animation: toastIn 0.2s ease-out;
      min-width: 260px;
      max-width: 420px;
    }
    @keyframes toastIn {
      from { transform: translateY(10px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    .toast-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 700;
      flex-shrink: 0;
    }
    .toast-success .toast-tag { color: #22c55e; }
    .toast-error .toast-tag { color: #ef4444; }
    .toast-info .toast-tag { color: #38bdf8; }

    /* Chronological Pipeline Stepper */
    .pipeline-steps-grid {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .pipeline-step-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: #050505;
      border: 1px solid #1a1a1a;
      border-radius: 6px;
      transition: all 0.2s ease;
    }
    .pipeline-step-item.running {
      border-color: #eab308;
      background: #0d0c04;
      box-shadow: 0 0 12px rgba(234, 179, 8, 0.15);
    }
    .pipeline-step-item.completed {
      border-color: #22c55e;
      background: #040c06;
    }
    .pipeline-step-item.failed {
      border-color: #ef4444;
      background: #0d0404;
    }
    .pipeline-step-idx {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #141414;
      color: #a0a0a0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      margin-right: 12px;
      flex-shrink: 0;
    }
    .pipeline-step-item.running .pipeline-step-idx {
      background: #eab308;
      color: #000000;
      animation: pulseStep 1s infinite alternate;
    }
    @keyframes pulseStep {
      from { transform: scale(1); }
      to { transform: scale(1.1); }
    }
    .pipeline-step-item.completed .pipeline-step-idx {
      background: #22c55e;
      color: #000000;
    }
    .pipeline-step-item.failed .pipeline-step-idx {
      background: #ef4444;
      color: #ffffff;
    }
    .pipeline-step-title {
      font-size: 0.82rem;
      font-weight: 600;
      color: #ffffff;
    }
    .pipeline-step-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .pipeline-step-badge {
      font-size: 0.70rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 3px 8px;
      border-radius: 4px;
      background: #121212;
      color: #888888;
      text-transform: uppercase;
      font-weight: 600;
    }
    .pipeline-step-item.running .pipeline-step-badge {
      background: rgba(234, 179, 8, 0.2);
      color: #eab308;
    }
    .pipeline-step-item.completed .pipeline-step-badge {
      background: rgba(34, 197, 94, 0.2);
      color: #22c55e;
    }
    .pipeline-step-item.failed .pipeline-step-badge {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }

    /* Chat Tags & Staff */
    .cs2-hud-chat-box {
      background: rgba(8, 8, 12, 0.94);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.04);
      border-radius: 6px;
      padding: 12px 16px;
      font-family: 'JetBrains Mono', 'Segoe UI', -apple-system, sans-serif;
    }
    .cs2-chat-line {
      font-size: 0.82rem;
      line-height: 1.55;
      letter-spacing: 0.01em;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);
      word-break: break-word;
    }
    .staff-card {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transition: border-color 0.15s ease;
    }
    .staff-card.has-overlap {
      border-color: rgba(234, 179, 8, 0.4);
      background: rgba(234, 179, 8, 0.03);
    }
    .tag-badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: #111111;
    }
    .color-chip {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.70rem;
      font-family: 'JetBrains Mono', monospace;
      cursor: pointer;
      background: #0d0d0d;
      border: 1px solid var(--card-border);
      transition: all 0.15s ease;
    }
    .color-chip:hover {
      background: #18181b;
      border-color: #3f3f46;
      transform: translateY(-1px);
    }
    .color-chip-swatch {
      width: 8px;
      height: 8px;
      border-radius: 2px;
    }
  
    /* MVP Studio Minimal Vinyl & Waveform Styles (Pitch-Black Luxury) */
    .mvp-queue-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 16px;
      padding: 12px 16px;
      background: #020202;
      border: 1px solid var(--card-border);
      border-radius: 6px;
    }
    .mvp-queue-count {
      font-size: 0.82rem;
      font-weight: 600;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .mvp-queue-badge {
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 12px;
      background: #111;
      border: 1px solid #27272a;
      color: #22c55e;
      font-family: 'JetBrains Mono', monospace;
    }
    .mvp-track-card {
      background: #030303;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .mvp-track-card:hover {
      border-color: #27272a;
    }
    .mvp-card-top {
      display: flex;
      gap: 16px;
      align-items: flex-start;
    }
    .mvp-vinyl-jacket {
      width: 76px;
      height: 76px;
      min-width: 76px;
      background: #000;
      border: 1px solid #1a1a1a;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      cursor: pointer;
      box-shadow: inset 0 0 12px rgba(0,0,0,0.9);
    }
    .mvp-vinyl-disc {
      width: 68px;
      height: 68px;
      border-radius: 50%;
      background: repeating-radial-gradient(circle, #222 0, #222 2px, #121212 3px, #121212 4px);
      border: 2px solid #2a2a2a;
      box-shadow: 0 4px 12px rgba(0,0,0,0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: transform 0.2s ease;
    }
    .mvp-vinyl-disc.spinning {
      animation: spinVinyl 3.5s linear infinite;
    }
    @keyframes spinVinyl {
      100% { transform: rotate(360deg); }
    }
    .mvp-vinyl-center {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: #141005;
      border: 1.5px solid #d4af37;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .mvp-vinyl-play-icon {
      width: 0;
      height: 0;
      border-top: 4px solid transparent;
      border-bottom: 4px solid transparent;
      border-left: 6px solid #d4af37;
      margin-left: 2px;
    }
    .mvp-vinyl-disc.spinning .mvp-vinyl-play-icon {
      border-top: 4px solid transparent;
      border-bottom: 4px solid transparent;
      border-left: 6px solid #22c55e;
    }
    .mvp-track-info {
      flex: 1;
      min-width: 0;
    }
    .mvp-track-badges {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 6px;
    }
    .mvp-pill {
      font-size: 0.68rem;
      padding: 2px 7px;
      border-radius: 4px;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .mvp-pill-green {
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid rgba(34, 197, 94, 0.3);
      color: #22c55e;
    }
    .mvp-pill-subtle {
      background: #090909;
      border: 1px solid #1a1a1a;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }
    .mvp-pill-event {
      background: #090909;
      border: 1px solid #1a1a1a;
      color: #38bdf8;
      font-family: 'JetBrains Mono', monospace;
    }
    .mvp-title-input {
      width: 100%;
      font-size: 0.96rem;
      font-weight: 700;
      color: #ffffff;
      background: transparent;
      border: none;
      border-bottom: 1px solid #1c1c1c;
      border-radius: 0;
      padding: 3px 0;
      margin-bottom: 6px;
      transition: border-color 0.2s ease;
    }
    .mvp-title-input:focus {
      border-bottom-color: #22c55e;
      outline: none;
    }
    .mvp-hud-box {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #000000;
      border: 1px solid #161616;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 0.74rem;
      color: #d4d4d8;
    }
    .mvp-hud-tag {
      background: #0369a1;
      color: #ffffff;
      font-size: 0.62rem;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 2px;
      letter-spacing: 0.04em;
    }
    .mvp-time-readout {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      font-weight: 600;
      color: #ededed;
      text-align: right;
      white-space: nowrap;
    }
    .mvp-waveform-wrap {
      position: relative;
      height: 48px;
      background: #010101;
      border: 1px solid #141414;
      border-radius: 6px;
      overflow: hidden;
      cursor: pointer;
      display: flex;
      align-items: center;
      padding: 0 4px;
    }
    .mvp-waveform-bars {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 2px;
      pointer-events: none;
    }
    .mvp-wave-bar {
      flex: 1;
      min-width: 2px;
      max-width: 4px;
      background: linear-gradient(180deg, #10b981 0%, #06b6d4 100%);
      border-radius: 2px;
      opacity: 0.55;
      transition: opacity 0.15s ease, height 0.2s ease;
    }
    .mvp-wave-bar.active-slice {
      opacity: 1;
      filter: drop-shadow(0 0 3px rgba(16, 185, 129, 0.6));
    }
    .mvp-cut-overlay {
      position: absolute;
      top: 0;
      bottom: 0;
      background: rgba(16, 185, 129, 0.12);
      border-left: 2px solid #10b981;
      border-right: 2px solid #06b6d4;
      pointer-events: none;
      transition: left 0.1s linear, width 0.1s linear;
    }
    .mvp-slider-track-wrap {
      position: relative;
      margin-top: 4px;
    }
    .mvp-scrubber-slider {
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 6px;
      background: #121212;
      border-radius: 3px;
      outline: none;
      margin: 0;
      cursor: pointer;
    }
    .mvp-scrubber-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #ffffff;
      box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
      cursor: pointer;
      transition: transform 0.1s ease;
    }
    .mvp-scrubber-slider::-webkit-slider-thumb:hover {
      transform: scale(1.2);
    }
    .mvp-controls-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 4px;
      padding-top: 8px;
      border-top: 1px solid #121212;
    }
    .mvp-btn-playback {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #0d0d0d;
      border: 1px solid #222;
      color: #fff;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    .mvp-btn-playback:hover {
      background: #181818;
      border-color: #333;
    }
    .mvp-duration-control {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #020202;
      border: 1px solid #141414;
      padding: 4px 10px;
      border-radius: 4px;
    }
    .mvp-dur-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      white-space: nowrap;
    }
    .mvp-dur-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.76rem;
      font-weight: 700;
      color: #22c55e;
      min-width: 38px;
    }
    .mvp-dur-slider {
      -webkit-appearance: none;
      appearance: none;
      width: 80px;
      height: 4px;
      background: #222;
      border-radius: 2px;
      outline: none;
    }
    .mvp-dur-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #22c55e;
      cursor: pointer;
    }
    .mvp-volume-control {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: #050505;
      border: 1px solid #1a1a1a;
      padding: 4px 10px;
      border-radius: 4px;
      transition: border-color 0.15s ease;
    }
    .mvp-volume-control:hover {
      border-color: #2a2a2a;
    }
    .mvp-vol-btn {
      cursor: pointer;
      display: flex;
      align-items: center;
      color: var(--text-muted);
      transition: color 0.15s;
    }
    .mvp-vol-btn:hover {
      color: #38bdf8;
    }
    .mvp-vol-slider {
      -webkit-appearance: none;
      appearance: none;
      width: 68px;
      height: 4px;
      background: #222;
      border-radius: 2px;
      outline: none;
      cursor: pointer;
      margin: 0;
    }
    .mvp-vol-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #38bdf8;
      box-shadow: 0 0 4px rgba(56, 189, 248, 0.5);
      cursor: pointer;
      transition: transform 0.1s ease;
    }
    .mvp-vol-slider::-webkit-slider-thumb:hover {
      transform: scale(1.2);
    }
    .mvp-vol-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      font-weight: 600;
      color: #38bdf8;
      min-width: 30px;
      text-align: right;
    }
    .btn-batch-deploy {
      background: #22c55e !important;
      color: #000000 !important;
      font-weight: 700 !important;
      font-size: 0.92rem !important;
      padding: 12px 28px !important;
      border: none !important;
      border-radius: 6px !important;
      cursor: pointer;
      transition: opacity 0.15s, transform 0.1s;
    }
    .btn-batch-deploy:hover {
      opacity: 0.92;
      transform: translateY(-1px);
    }
</style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">CS2</div>
      <div>
        <div class="brand-title">Server Control Center</div>
        <div class="brand-sub">81.181.113.120:27015 | talent.walliez.xyz</div>
      </div>
    </div>
    <div class="status-badge" id="headerStatusBadge">
      <span class="status-dot"></span>
      <span id="headerStatusText">Checking Server...</span>
    </div>
  </header>

  <div class="app-container">

    <!-- Navigation Tabs -->
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-announcements')">Announcements</button>
      <button class="tab-btn" onclick="switchTab('tab-tags')">Chat Tags & Staff</button>
      <button class="tab-btn" onclick="switchTab('tab-hostname')">Server Name</button>
      <button class="tab-btn" onclick="switchTab('tab-convars')">Match Convars</button>
      <button class="tab-btn" onclick="switchTab('tab-mvp')">MVP Anthems</button>
      <button class="tab-btn" onclick="switchTab('tab-services')">Services & Bot</button>
    </div>

    <!-- TAB 1: Announcements Manager -->
    <div id="tab-announcements" class="tab-content active">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">ServerAnnouncer Settings</div>
            <div class="card-desc">Scheduled in-game chat messages promoting skinz, mvpz, and community links.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadAnnouncements()">Reload Config</button>
        </div>

        <div class="input-row">
          <div class="form-group">
            <label>Interval (Seconds)</label>
            <input type="number" id="announcerInterval" min="15" max="600" value="90">
          </div>
          <div class="form-group">
            <label>Rotation Mode</label>
            <select id="announcerRandom">
              <option value="true">Random Order (Non-Repeating)</option>
              <option value="false">Sequential Order (List Sequence)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Announcement Prefix</label>
          <input type="text" id="announcerPrefix" value="{Gold}[Walliez]{Default}" oninput="updateChatPreview()">
          <div class="color-tags-container">
            <span class="color-tag-pill" onclick="insertColorTag('{Gold}')" style="color: #E4AE39;">{Gold}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightBlue}')" style="color: #5E98D9;">{LightBlue}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Green}')" style="color: #40FF40;">{Green}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightPurple}')" style="color: #D32CE6;">{LightPurple}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightYellow}')" style="color: #E5E24D;">{LightYellow}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Red}')" style="color: #FF4040;">{Red}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Default}')" style="color: #FFFFFF;">{Default}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Grey}')" style="color: #CCCCCC;">{Grey}</span>
          </div>
        </div>

        <div class="card-header" style="margin-top: 18px; margin-bottom: 10px;">
          <div class="card-title" style="font-size: 0.84rem;">Active Announcement Messages</div>
          <button class="btn btn-sm" onclick="addNewMessagePrompt()">Add Message</button>
        </div>

        <div class="msg-list" id="announcementsList">
          <div style="color: var(--text-muted); font-size: 0.8rem;">Loading messages...</div>
        </div>

        <div class="cs2-chat-label">Live In-Game Chat Simulator Preview:</div>
        <div class="cs2-chat-sim">
          <div class="cs2-preview-text" id="cs2ChatSimPreview">Previewing announcement...</div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end; gap: 8px;">
          <button class="btn btn-secondary" onclick="loadAnnouncements()">Cancel</button>
          <button class="btn" onclick="saveAnnouncementsToServer()">Save & Deploy Live</button>
        </div>
      </div>
    </div>
    <!-- TAB: Chat Tags & Staff Roles -->
    <div id="tab-tags" class="tab-content">
      
      <!-- Top Overview & Live Simulation -->
      <div class="card" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
          <div>
            <div class="card-title">CS2 In-Game Chat Live Simulation</div>
            <div class="card-desc">Authentic Counter-Strike 2 in-game chat HUD rendering staff tags, player names, and message colors.</div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-sm" id="btnPreviewStream" onclick="setChatPreviewMode('stream')">Staff Conversation</button>
            <button class="btn btn-sm btn-secondary" id="btnPreviewSandbox" onclick="setChatPreviewMode('sandbox')">Interactive Sandbox</button>
          </div>
        </div>

        <!-- In-Game Chat HUD Box -->
        <div class="cs2-hud-chat-box" style="margin-top: 14px;">
          <!-- Mode 1: Simulated Multi-Role Staff Conversation -->
          <div id="cs2ChatStreamContainer" style="display: flex; flex-direction: column; gap: 5px;"></div>

          <!-- Mode 2: Interactive Sandbox Tester -->
          <div id="cs2ChatSandboxContainer" style="display: none; flex-direction: column; gap: 10px;">
            <div id="cs2SandboxPreviewLine" class="cs2-chat-line" style="padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.08); min-height: 24px;"></div>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end; background: rgba(0,0,0,0.5); border: 1px solid var(--card-border); padding: 10px 12px; border-radius: 6px;">
              <div style="width: 140px;">
                <label style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 4px; display: block;">Select Tag / Role</label>
                <select id="sandboxRoleSelect" class="form-control" style="height: 28px; font-size: 0.76rem;" onchange="onSandboxRoleChanged()"></select>
              </div>
              <div style="width: 130px;">
                <label style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 4px; display: block;">Player Name</label>
                <input type="text" id="sandboxPlayerName" value="doggg" class="form-control" style="height: 28px; font-size: 0.76rem;" oninput="updateSandboxPreview()">
              </div>
              <div style="flex: 1; min-width: 180px;">
                <label style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 4px; display: block;">Sample Message</label>
                <input type="text" id="sandboxMessage" value="Welcome to the server! Good luck and have fun." class="form-control" style="height: 28px; font-size: 0.76rem;" oninput="updateSandboxPreview()">
              </div>
              <div style="display: flex; gap: 10px; align-items: center; height: 28px;">
                <label style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #f87171; cursor: pointer;">
                  <input type="checkbox" id="sandboxDeadToggle" onchange="updateSandboxPreview()"> [DEAD]
                </label>
                <label style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #a1a1aa; cursor: pointer;">
                  <input type="radio" name="sandboxTeam" value="all" checked onchange="updateSandboxPreview()"> All
                </label>
                <label style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #38bdf8; cursor: pointer;">
                  <input type="radio" name="sandboxTeam" value="ct" onchange="updateSandboxPreview()"> CT
                </label>
                <label style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #fbbf24; cursor: pointer;">
                  <input type="radio" name="sandboxTeam" value="t" onchange="updateSandboxPreview()"> T
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Staff Overlaps & Role Resolver -->
      <div class="card" style="margin-bottom: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div>
            <div class="card-title">Server Staff & Role Assignments</div>
            <div class="card-desc">Automatically inspects server administrators from <code style="font-size:0.75rem;">admins.json</code>. Resolves overlapping staff roles if multiple groups apply.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadTagsAndStaff()">Refresh Staff</button>
        </div>
        <div id="staffListContainer" style="display: flex; flex-direction: column; gap: 8px;">
          <div style="color: var(--text-muted); font-size: 0.8rem; padding: 12px; text-align: center;">Loading staff members from server...</div>
        </div>
      </div>

      <!-- Configured Tags Table -->
      <div class="card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div>
            <div class="card-title">Configured Chat Tags</div>
            <div class="card-desc">Edit existing tags, add custom group/SteamID tags, and select CS2 colors.</div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-sm btn-secondary" onclick="openAddTagModal()">+ Add Custom Tag</button>
            <button class="btn btn-sm" onclick="saveAllTagsAndStaff()">Save Changes & Reload</button>
          </div>
        </div>

        <!-- Color Palette Quick Swatches -->
        <div style="margin-bottom: 14px; background: #060606; border: 1px solid var(--card-border); border-radius: 6px; padding: 10px 12px;">
          <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em;">
            Quick Color Palette (Click to insert into selected input)
          </div>
          <div class="color-tags-container" id="chatTagColorPalette"></div>
        </div>

        <!-- Tags Table -->
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.78rem;">
            <thead>
              <tr style="border-bottom: 1px solid var(--card-border); text-align: left; color: var(--text-muted);">
                <th style="padding: 8px 10px;">Role / Target Key</th>
                <th style="padding: 8px 10px;">Chat Tag</th>
                <th style="padding: 8px 10px;">Name Color</th>
                <th style="padding: 8px 10px;">Chat Color</th>
                <th style="padding: 8px 10px;">In-Game Live Render</th>
                <th style="padding: 8px 10px; text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody id="tagsTableBody">
              <tr><td colspan="6" style="text-align:center; padding:16px; color:var(--text-muted);">Loading tags...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>


    <!-- TAB 2: Server Hostname & Title -->
    <div id="tab-hostname" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Server Hostname & Title</div>
            <div class="card-desc">Instantly updates the live CS2 server name via RCON and saves permanently to server.cfg.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadHostname()">Query Live Name</button>
        </div>

        <div class="form-group">
          <label>Server Hostname</label>
          <input type="text" id="serverHostnameInput" placeholder="Counter-Strike 2 Server" oninput="updateHostnamePreview()">
        </div>

        <div class="cs2-chat-label" style="margin-top: 14px;">Steam & CS2 Server Browser Preview:</div>
        <div style="background: #040404; border: 1px solid var(--card-border); border-radius: 6px; padding: 14px; margin-top: 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;">
            <div style="font-weight: 600; font-size: 0.95rem; color: #ffffff;" id="hostnamePreviewText">talent.walliez.xyz</div>
            <div style="font-size: 0.76rem; color: #22c55e; font-family: 'JetBrains Mono', monospace;">Online | 81.181.113.120:27015</div>
          </div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveHostname()">Apply Hostname</button>
        </div>
      </div>
    </div>

    <!-- TAB 3: Match Settings & Convars -->
    <div id="tab-convars" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Match Settings & Convar Editor</div>
            <div class="card-desc">Tune round timers, overtime, economy, and competitive match rules.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadConvars()">Fetch Convars</button>
        </div>

        <div class="form-group">
          <input type="text" id="convarSearch" placeholder="Search convars by name or description..." oninput="filterConvars()">
        </div>

        <div class="convars-grid" id="convarsGrid">
          <!-- Populated by JS -->
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveConvars()">Apply Convar Settings</button>
        </div>
      </div>
    </div>

    <!-- TAB 4: All-in-One MVP Creator & Workshop Deployer -->
    <div id="tab-mvp" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">All-in-One MVP Creator & Workshop Deployer</div>
            <div class="card-desc">Batch queue multiple songs, scrub start timestamps, choose custom MVP durations, and compile/deploy all anthems in one unified pipeline.</div>
          </div>
          <div class="status-badge" style="background:#0a0a0a; border-color:var(--card-border);">
            <span class="status-dot"></span>
            <span>Addon: wlzMVP (3827657422)</span>
          </div>
        </div>

        <div class="summary-grid" style="margin-bottom: 20px;">
          <div class="summary-card">
            <div class="summary-label">Audio Standard</div>
            <div class="summary-val" style="font-size:0.82rem; color:#fff;">Custom Durations (5-15s) | 1.0s Fadeout | 44.1kHz PCM WAV</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Source 2 SoundEvent</div>
            <div class="summary-val" style="font-size:0.82rem; color:#fff;">CustomMVP.{id} -> sounds/mvp/{id}.vsnd_c</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Game Display</div>
            <div class="summary-val" style="font-size:0.82rem; color:#fff;">WASD /mvp Menu & Winner Chat Broadcast</div>
          </div>
        </div>

        <!-- MVP Batch Queue Toolbar -->
        <div class="mvp-queue-toolbar">
          <div class="mvp-queue-count">
            <span>MVP Anthems Queue</span>
            <span class="mvp-queue-badge" id="mvpQueueCountBadge">0 Tracks</span>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn-sm" style="background:#22c55e; color:#000; font-weight:700;" onclick="browseMvpMultipleFiles()">
              + Select Audio Files
            </button>
            <button class="btn btn-sm btn-secondary" onclick="addBlankTrackToQueue()">
              + Add Track Manually
            </button>
            <button class="btn btn-sm btn-secondary" onclick="clearMvpQueue()">
              Clear Queue
            </button>
          </div>
        </div>

        <!-- Track Cards Queue Container -->
        <div id="mvpQueueContainer">
          <!-- Populated dynamically by JS -->
        </div>

        <!-- Master Batch Execution Bar -->
        <div id="mvpBatchActionBar" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; background: #040404; border: 1px solid var(--card-border); border-radius: 6px; padding: 16px; margin-bottom: 20px;">
          <div>
            <div style="font-weight: 700; color: #fff; font-size: 0.9rem;" id="mvpBatchSummaryTitle">0 Anthems Ready to Convert</div>
            <div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
              Executes mastering, KV3 soundevents update, asset compilation, server registration, and VPK deployment for all queued tracks simultaneously.
            </div>
          </div>
          <button class="btn btn-batch-deploy" id="btnRunMvpBatchPipeline" onclick="runMvpBatchPipeline()">
            Convert & Deploy All to Server
          </button>
        </div>

        <!-- Chronological Pipeline Stepper Tracker -->
        <div id="mvpPipelineTracker" style="display:none; background: #030303; border: 1px solid var(--card-border); border-radius: 6px; padding: 18px; margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div style="font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #fff;">
              Pipeline Execution Status
            </div>
            <div id="pipelineOverallStatus" style="font-size: 0.76rem; font-family: 'JetBrains Mono', monospace; color: var(--gold);">
              Initializing...
            </div>
          </div>

          <div class="pipeline-steps-grid" id="pipelineStepsList">
            <!-- Populated by JS -->
          </div>

          <!-- Workshop Update Action Banner (appears upon Step 7) -->
          <div id="workshopReadyBanner" style="display:none; margin-top: 18px; padding: 14px 18px; background: #080808; border: 1px solid #22c55e; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
              <div>
                <div style="font-weight: 700; color: #22c55e; font-size: 0.92rem;">Ready for Steam Workshop Update!</div>
                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
                  All assets are compiled into wlzMVP and synchronized across the server. Launch CS2 Workshop Tools to submit the update.
                </div>
              </div>
              <button class="btn" style="background: #22c55e; color: #000; font-weight: 700;" onclick="launchWorkshopTools()">
                Launch CS2 Workshop Tools
              </button>
            </div>
          </div>
        </div>

        <!-- Active Server Anthems Table -->
        <div style="margin-top: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
              <div style="font-weight: 600; font-size: 0.92rem; color: #fff;">Active Server Anthems</div>
              <div style="font-size: 0.74rem; color: var(--text-muted);">Anthems registered in MVP_Settings.json and available in /mvp.</div>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-sm btn-secondary" onclick="loadMvpList()">Refresh List</button>
              <button class="btn btn-sm btn-secondary" onclick="triggerClientSync()">Sync Local CS2</button>
              <button class="btn btn-sm btn-secondary" onclick="triggerWorkshopRebuild()">Rebuild All</button>
              <button class="btn btn-sm btn-secondary" onclick="launchWorkshopTools()">CS2 Tools</button>
            </div>
          </div>

          <div style="border: 1px solid var(--card-border); border-radius: 6px; overflow: hidden;">
            <table class="services-table" style="width: 100%;">
              <thead>
                <tr>
                  <th style="padding: 10px 14px;">Kit / Anthem Name</th>
                  <th style="padding: 10px 14px;">SoundEvent Identifier</th>
                  <th style="padding: 10px 14px;">Duration</th>
                  <th style="padding: 10px 14px;">Binary Resource Path</th>
                  <th style="padding: 10px 14px; text-align: right;">Action</th>
                </tr>
              </thead>
              <tbody id="mvpAnthemsTableBody">
                <!-- Dynamically populated -->
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

    <!-- TAB 5: Services & Discord Bot -->
    <div id="tab-services" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">VPS Services & Discord Bot</div>
            <div class="card-desc">Control server services, restart processes, and verify connectivity.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="refreshServices()">Refresh Status</button>
        </div>

        <div class="services-grid">
          <div class="service-card">
            <div>
              <div class="summary-label">CS2 Game Server</div>
              <div class="summary-val" id="statCs2Status" style="color: #22c55e;">Active (Running)</div>
            </div>
            <button class="btn btn-danger" onclick="serviceAction('restart_cs2')">Restart CS2 Server</button>
          </div>
          <div class="service-card">
            <div>
              <div class="summary-label">Discord 24/7 Bot</div>
              <div class="summary-val" id="statBotStatus" style="color: #22c55e;">Active (Running)</div>
            </div>
            <button class="btn btn-secondary" onclick="serviceAction('restart_bot')">Restart Discord Bot</button>
          </div>
          <div class="service-card">
            <div>
              <div class="summary-label">CSS Plugins Core</div>
              <div class="summary-val" style="color: #ffffff;">Loaded</div>
            </div>
            <button class="btn btn-secondary" onclick="serviceAction('reload_plugins')">Reload All Plugins</button>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <label style="margin-bottom: 8px;">Direct Panel Links</label>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="https://skinz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm">Skin & Knife Panel</a>
            <a href="https://mvpz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm">MVP Anthems Panel</a>
            <a href="https://skinz.walliez.xyz/connect/" target="_blank" class="btn btn-secondary btn-sm">Steam Connect Page</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Log Terminal Drawer -->
    <div class="card" style="padding: 14px; margin-bottom: 0;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Activity Log</div>
        <button class="btn btn-sm btn-secondary" style="height: 22px; padding: 0 8px; font-size: 0.68rem;" onclick="clearLogs()">Clear</button>
      </div>
      <div class="terminal-drawer" id="terminalLog">Control Center ready. Connected to 81.181.113.120.</div>
    </div>

  </div>

  <!-- In-App Modal Dialogs -->
  <!-- Announcement Edit/Add Modal -->
  <div class="modal-overlay" id="announcementModal">
    <div class="modal-card">
      <div class="modal-header">
        <div class="modal-title" id="announcementModalTitle">Edit Announcement Message</div>
        <button class="modal-close-btn" onclick="closeAnnouncementModal()">&times;</button>
      </div>
      <div class="modal-body">
        <label>Announcement Text</label>
        <textarea id="modalMsgInput" rows="3" placeholder="Enter message text... (use color tags below)" oninput="updateModalPreview()"></textarea>
        <div>
          <label style="font-size:0.68rem; margin-bottom:4px;">Quick Color Tags</label>
          <div class="color-tags-container" style="margin-top:0;">
            <span class="color-tag-pill" onclick="insertModalColor('{Gold}')" style="color: #E4AE39;">{Gold}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{LightBlue}')" style="color: #5E98D9;">{LightBlue}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{Green}')" style="color: #40FF40;">{Green}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{LightPurple}')" style="color: #D32CE6;">{LightPurple}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{LightYellow}')" style="color: #E5E24D;">{LightYellow}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{Red}')" style="color: #FF4040;">{Red}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{Default}')" style="color: #FFFFFF;">{Default}</span>
            <span class="color-tag-pill" onclick="insertModalColor('{Grey}')" style="color: #CCCCCC;">{Grey}</span>
          </div>
        </div>
        <div>
          <label style="font-size:0.68rem; margin-bottom:4px;">In-Game Preview</label>
          <div class="cs2-chat-sim" style="min-height:38px; margin-top:0; padding:8px 12px;">
            <div class="cs2-preview-text" id="modalChatPreview" style="font-size:0.84rem;">Preview...</div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeAnnouncementModal()">Cancel</button>
        <button class="btn" onclick="saveAnnouncementModal()">Save Message</button>
      </div>
    </div>
  </div>

  <!-- Confirmation Modal -->
  <div class="modal-overlay" id="confirmModal">
    <div class="modal-card" style="max-width: 440px;">
      <div class="modal-header">
        <div class="modal-title" id="confirmModalTitle">Confirm Action</div>
        <button class="modal-close-btn" onclick="closeConfirmModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div id="confirmModalMsg" style="font-size: 0.82rem; color: #d4d4d8; line-height: 1.5;">Are you sure?</div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeConfirmModal()">Cancel</button>
        <button class="btn btn-danger" id="confirmModalBtn" onclick="executeConfirmAction()">Confirm</button>
      </div>
    </div>
  </div>

  <!-- Audio Converter Modal -->
  <div class="modal-overlay" id="converterModal">
    <div class="modal-card" style="max-width: 480px;">
      <div class="modal-header">
        <div class="modal-title">Convert Audio to Clean 44.1kHz MP3</div>
        <button class="modal-close-btn" onclick="closeConverterModal()">&times;</button>
      </div>
      <div class="modal-body">
        <label>Audio File Path</label>
        <input type="text" id="converterPathInput" placeholder="C:\\path\\to\\audio.mp3">
        <div style="font-size:0.72rem; color:var(--text-muted); line-height:1.4;">
          Converts using the exact onlineaudioconverter.com 320kbps 44.1kHz CBR algorithm with ID3 metadata stripped and 10.0s trim.
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeConverterModal()">Cancel</button>
        <button class="btn" onclick="submitConvertFile()">Convert File</button>
      </div>
    </div>
  </div>

  <!-- Add Custom Tag Modal -->
  <div class="modal-overlay" id="addTagModal">
    <div class="modal-card" style="max-width: 480px;">
      <div class="modal-header">
        <div class="modal-title">Add Custom Chat Tag</div>
        <button class="modal-close-btn" onclick="closeAddTagModal()">&times;</button>
      </div>
      <div class="modal-body" style="display: flex; flex-direction: column; gap: 12px;">
        <div>
          <label style="font-size: 0.72rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Role / Target Key</label>
          <input type="text" id="newTagKeyInput" placeholder="e.g. #wlz/vip, #supporter, or 76561199123456789" class="form-control" style="font-family: 'JetBrains Mono', monospace;">
          <div style="font-size: 0.68rem; color: var(--text-muted); margin-top: 3px;">Prefix with '#' for Admin Group, or enter a 17-digit SteamID64 for player-specific tag.</div>
        </div>
        <div>
          <label style="font-size: 0.72rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Chat Tag Text</label>
          <input type="text" id="newTagTextInput" placeholder="{Gold}[VIP]" class="form-control" oninput="updateNewTagModalPreview()">
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div>
            <label style="font-size: 0.72rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Player Name Color</label>
            <input type="text" id="newTagNameColorInput" value="{Gold}" class="form-control" oninput="updateNewTagModalPreview()">
          </div>
          <div>
            <label style="font-size: 0.72rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Chat Text Color</label>
            <input type="text" id="newTagChatColorInput" value="{White}" class="form-control" oninput="updateNewTagModalPreview()">
          </div>
        </div>
        <div>
          <label style="font-size: 0.72rem; color: var(--text-muted); display: block; margin-bottom: 4px;">Live In-Game Preview</label>
          <div class="cs2-hud-chat-box" style="padding: 10px 14px; min-height: 40px;" id="newTagModalPreview">
            <!-- Rendered in real time -->
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeAddTagModal()">Cancel</button>
        <button class="btn" onclick="submitAddCustomTag()">Add Tag</button>
      </div>
    </div>
  </div>

  <!-- Toast Notification Container -->
  <div class="toast-container" id="toastContainer"></div>

  <script>
    function log(text) {
      const term = document.getElementById('terminalLog');
      const time = new Date().toLocaleTimeString();
      term.innerHTML += `\\n[${time}] ${text}`;
      term.scrollTop = term.scrollHeight;
    }
    function clearLogs() {
      document.getElementById('terminalLog').innerHTML = 'Log cleared.';
    }

    function switchTab(tabId, btn = null) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      const contentEl = document.getElementById(tabId);
      if (contentEl) contentEl.classList.add('active');
      const activeBtn = btn || (typeof event !== 'undefined' && event && event.target && event.target.classList && event.target.classList.contains('tab-btn') ? event.target : document.querySelector(`.tab-btn[onclick*="${tabId}"]`));
      if (activeBtn) activeBtn.classList.add('active');
      if (tabId === 'tab-announcements') loadAnnouncements();
      if (tabId === 'tab-tags') loadTagsAndStaff();
      if (tabId === 'tab-hostname') loadHostname();
      if (tabId === 'tab-convars') loadConvars();
      if (tabId === 'tab-mvp') {
        loadMvpList();
        renderMvpQueue();
      }
      if (tabId === 'tab-services') refreshServices();
    }

    // In-App Toast System
    function showToast(msg, type = 'success') {
      const container = document.getElementById('toastContainer');
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      const tag = type === 'success' ? '[OK]' : (type === 'error' ? '[ERROR]' : '[INFO]');
      toast.innerHTML = `<span class="toast-tag">${tag}</span><span>${msg}</span>`;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.transition = 'opacity 0.2s, transform 0.2s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        setTimeout(() => toast.remove(), 250);
      }, 3500);
    }

    // In-App Modal Dialog Management
    let editingMessageIndex = -1;

    function openAnnouncementModal(idx = -1) {
      editingMessageIndex = idx;
      const titleEl = document.getElementById('announcementModalTitle');
      const inputEl = document.getElementById('modalMsgInput');
      if (idx >= 0 && announcementsData.Messages[idx]) {
        titleEl.innerText = `Edit Announcement Message #${idx + 1}`;
        inputEl.value = announcementsData.Messages[idx];
      } else {
        titleEl.innerText = 'New Announcement Message';
        inputEl.value = '';
      }
      updateModalPreview();
      document.getElementById('announcementModal').classList.add('active');
      inputEl.focus();
    }

    function closeAnnouncementModal() {
      document.getElementById('announcementModal').classList.remove('active');
    }

    function insertModalColor(tag) {
      const input = document.getElementById('modalMsgInput');
      const start = input.selectionStart || input.value.length;
      const end = input.selectionEnd || input.value.length;
      const text = input.value;
      input.value = text.substring(0, start) + tag + text.substring(end);
      input.focus();
      input.setSelectionRange(start + tag.length, start + tag.length);
      updateModalPreview();
    }

    function updateModalPreview() {
      const val = document.getElementById('modalMsgInput').value || 'Enter text to preview...';
      const prefix = document.getElementById('announcerPrefix').value || '';
      document.getElementById('modalChatPreview').innerHTML = parseCs2Colors((prefix ? prefix + ' ' : '') + val);
    }

    function saveAnnouncementModal() {
      const val = document.getElementById('modalMsgInput').value.trim();
      if (!val) {
        showToast('Message text cannot be empty.', 'error');
        return;
      }
      if (editingMessageIndex >= 0) {
        announcementsData.Messages[editingMessageIndex] = val;
        log(`Updated announcement #${editingMessageIndex + 1}`);
      } else {
        announcementsData.Messages.push(val);
        log(`Added new announcement #${announcementsData.Messages.length}`);
      }
      renderAnnouncementsList();
      closeAnnouncementModal();
      showToast('Announcement updated. Click "Save & Deploy Live" to apply to server.', 'info');
    }

    // Confirmation Modal System
    let pendingConfirmAction = null;

    function openConfirmModal(title, msg, onConfirm, btnText = 'Confirm', isDanger = true) {
      document.getElementById('confirmModalTitle').innerText = title;
      document.getElementById('confirmModalMsg').innerText = msg;
      const btn = document.getElementById('confirmModalBtn');
      btn.innerText = btnText;
      btn.className = isDanger ? 'btn btn-danger' : 'btn';
      pendingConfirmAction = onConfirm;
      document.getElementById('confirmModal').classList.add('active');
    }

    function closeConfirmModal() {
      document.getElementById('confirmModal').classList.remove('active');
      pendingConfirmAction = null;
    }

    function executeConfirmAction() {
      if (pendingConfirmAction) {
        pendingConfirmAction();
      }
      closeConfirmModal();
    }

    // Audio Converter Modal
    function openConvertModal() {
      document.getElementById('converterPathInput').value = '';
      document.getElementById('converterModal').classList.add('active');
      document.getElementById('converterPathInput').focus();
    }

    function closeConverterModal() {
      document.getElementById('converterModal').classList.remove('active');
    }

    function submitConvertFile() {
      const p = document.getElementById('converterPathInput').value.trim();
      if (!p) {
        showToast('Please enter an audio file path.', 'error');
        return;
      }
      closeConverterModal();
      log(`Converting audio file: ${p}...`);
      fetch('/api/convert_mp3', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path: p})
      })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          log(d.output || 'Conversion complete.');
          showToast('Audio conversion complete.', 'success');
        } else {
          log('[ERROR] ' + (d.error || 'Conversion failed.'));
          showToast(d.error || 'Conversion failed.', 'error');
        }
      })
      .catch(e => {
        log('[ERROR] ' + e);
        showToast(String(e), 'error');
      });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeAnnouncementModal();
        closeConfirmModal();
        closeConverterModal();
      }
      if (e.key === 'Enter' && e.ctrlKey && document.getElementById('announcementModal').classList.contains('active')) {
        saveAnnouncementModal();
      }
    });

    // CS2 Color Parser
    const CS2_COLORS = {
      '{Default}': '#FFFFFF',
      '{White}': '#FFFFFF',
      '{DarkRed}': '#C42B2B',
      '{LightPurple}': '#D32CE6',
      '{Green}': '#40FF40',
      '{Olive}': '#A2B236',
      '{Lime}': '#A9FF00',
      '{Red}': '#FF4040',
      '{Grey}': '#CCCCCC',
      '{Gray}': '#CCCCCC',
      '{Yellow}': '#FFF200',
      '{LightYellow}': '#E5E24D',
      '{Gold}': '#E4AE39',
      '{Silver}': '#A1A1AA',
      '{Blue}': '#4D90CD',
      '{DarkBlue}': '#1E3A8A',
      '{LightBlue}': '#5E98D9',
      '{Magenta}': '#EB4B98',
      '{LightRed}': '#FF6B6B',
      '{Purple}': '#D32CE6',
      '{TeamColor}': '#5E98D9'
    };

    const TAG_COLOR_PALETTE = [
      { tag: '{DarkRed}', hex: '#C42B2B', label: 'Dark Red' },
      { tag: '{Red}', hex: '#FF4040', label: 'Red' },
      { tag: '{LightRed}', hex: '#FF6B6B', label: 'Light Red' },
      { tag: '{Green}', hex: '#40FF40', label: 'Green' },
      { tag: '{Lime}', hex: '#A9FF00', label: 'Lime' },
      { tag: '{Olive}', hex: '#A2B236', label: 'Olive' },
      { tag: '{LightPurple}', hex: '#D32CE6', label: 'Purple' },
      { tag: '{Gold}', hex: '#E4AE39', label: 'Gold' },
      { tag: '{Yellow}', hex: '#FFF200', label: 'Yellow' },
      { tag: '{LightBlue}', hex: '#5E98D9', label: 'Light Blue' },
      { tag: '{Blue}', hex: '#4D90CD', label: 'Blue' },
      { tag: '{DarkBlue}', hex: '#1E3A8A', label: 'Dark Blue' },
      { tag: '{Grey}', hex: '#CCCCCC', label: 'Grey' },
      { tag: '{White}', hex: '#FFFFFF', label: 'White' },
      { tag: '{TeamColor}', hex: '#5E98D9', label: 'Team Color' }
    ];

    let tagsData = {};
    let staffData = [];
    let staffAssignments = {};
    let chatPreviewMode = 'stream';
    let lastActiveColorInput = null;

    function renderCs2ChatLine(dead, team, tag, nameColor, chatColor, playerName, message) {
      let full = '';
      if (dead) full += '{Red}[DEAD] ';
      if (team === 'ct') full += '{LightBlue}(Counter-Terrorist) ';
      else if (team === 't') full += '{Gold}(Terrorist) ';
      if (tag) full += tag + ' ';
      full += (nameColor || '{White}') + playerName + '{Default}: ' + (chatColor || '{White}') + message;
      return parseCs2Colors(full);
    }

    async function loadTagsAndStaff() {
      log('Fetching chat tags and staff assignments from VPS...');
      try {
        const res = await fetch('/api/tags');
        const data = await res.json();
        if (data.success) {
          tagsData = data.tags || {};
          staffData = data.staff || [];
          staffAssignments = {};
          renderStaffList();
          renderTagsTable();
          renderChatTagColorPalette();
          renderChatSimulation();
          initSandboxRoleSelect();
          log('Chat tags and staff loaded successfully.');
        } else {
          log('[ERROR] Failed to load tags: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        log('[ERROR] Error fetching tags: ' + e);
      }
    }

    function setChatPreviewMode(mode) {
      chatPreviewMode = mode;
      const btnStream = document.getElementById('btnPreviewStream');
      const btnSandbox = document.getElementById('btnPreviewSandbox');
      const streamContainer = document.getElementById('cs2ChatStreamContainer');
      const sandboxContainer = document.getElementById('cs2ChatSandboxContainer');

      if (mode === 'stream') {
        if (btnStream) btnStream.className = 'btn btn-sm';
        if (btnSandbox) btnSandbox.className = 'btn btn-sm btn-secondary';
        if (streamContainer) streamContainer.style.display = 'flex';
        if (sandboxContainer) sandboxContainer.style.display = 'none';
        renderChatSimulation();
      } else {
        if (btnStream) btnStream.className = 'btn btn-sm btn-secondary';
        if (btnSandbox) btnSandbox.className = 'btn btn-sm';
        if (streamContainer) streamContainer.style.display = 'none';
        if (sandboxContainer) sandboxContainer.style.display = 'flex';
        updateSandboxPreview();
      }
    }

    function renderChatSimulation() {
      const stream = document.getElementById('cs2ChatStreamContainer');
      if (!stream) return;
      stream.innerHTML = '';

      const sampleMessages = [
        { role: '#wlz/owner', name: 'doggg', dead: false, team: 'all', msg: 'Welcome to talent.walliez.xyz! Type !ws or !mvp.' },
        { role: '#wlz/admin', name: 'Fiora', dead: false, team: 'ct', msg: 'Competitive MR12 match is live. Have fun and gl hf!' },
        { role: '#wlz/mod', name: 'Andreea3', dead: false, team: 'all', msg: 'Please keep chat clean and friendly.' },
        { role: 'Default', name: 'Guest_Player', dead: true, team: 't', msg: "rush B dont stop!" }
      ];

      for (const [k, tag] of Object.entries(tagsData)) {
        if (!['#wlz/owner', '#wlz/admin', '#wlz/mod', 'Default'].includes(k)) {
          sampleMessages.splice(3, 0, {
            role: k,
            name: k.startsWith('#') ? k.replace('#wlz/', '').replace('#', '') : 'VIP_Member',
            dead: false,
            team: 'all',
            msg: 'Enjoying custom anthems and skin features!'
          });
          break;
        }
      }

      sampleMessages.forEach(item => {
        const tag = tagsData[item.role] || tagsData['Default'] || { ChatTag: '', NameColor: '{White}', ChatColor: '{White}' };
        const line = document.createElement('div');
        line.className = 'cs2-chat-line';
        line.innerHTML = renderCs2ChatLine(item.dead, item.team, tag.ChatTag, tag.NameColor, tag.ChatColor, item.name, item.msg);
        stream.appendChild(line);
      });
    }

    function initSandboxRoleSelect() {
      const select = document.getElementById('sandboxRoleSelect');
      if (!select) return;
      select.innerHTML = '';
      for (const [k, tag] of Object.entries(tagsData)) {
        const opt = document.createElement('option');
        opt.value = k;
        opt.innerText = `${k} (${tag.ChatTag || 'No Tag'})`;
        select.appendChild(opt);
      }
      updateSandboxPreview();
    }

    function onSandboxRoleChanged() {
      const selVal = document.getElementById('sandboxRoleSelect')?.value || 'Default';
      const nameInput = document.getElementById('sandboxPlayerName');
      if (nameInput) {
        if (selVal === '#wlz/owner') nameInput.value = 'doggg';
        else if (selVal === '#wlz/admin') nameInput.value = 'Fiora';
        else if (selVal === '#wlz/mod') nameInput.value = 'Andreea3';
        else if (selVal === 'Default') nameInput.value = 'Player';
      }
      updateSandboxPreview();
    }

    function updateSandboxPreview() {
      const previewLine = document.getElementById('cs2SandboxPreviewLine');
      if (!previewLine) return;
      const roleKey = document.getElementById('sandboxRoleSelect')?.value || 'Default';
      const tag = tagsData[roleKey] || { ChatTag: '', NameColor: '{White}', ChatColor: '{White}' };
      const playerName = document.getElementById('sandboxPlayerName')?.value.trim() || 'Player';
      const msg = document.getElementById('sandboxMessage')?.value.trim() || 'Sample message';
      const isDead = document.getElementById('sandboxDeadToggle')?.checked || false;
      const teamVal = document.querySelector('input[name="sandboxTeam"]:checked')?.value || 'all';

      previewLine.innerHTML = renderCs2ChatLine(isDead, teamVal, tag.ChatTag, tag.NameColor, tag.ChatColor, playerName, msg);
    }

    function renderStaffList() {
      const container = document.getElementById('staffListContainer');
      if (!container) return;
      if (!staffData || staffData.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 12px; text-align: center;">No staff members configured in admins.json.</div>';
        return;
      }

      container.innerHTML = staffData.map(s => {
        const activeTag = tagsData[s.active_tag_key] || { ChatTag: '', NameColor: '{White}', ChatColor: '{White}' };
        const cleanName = s.name.split(' / ')[0];
        const previewHtml = renderCs2ChatLine(false, 'all', activeTag.ChatTag, activeTag.NameColor, activeTag.ChatColor, cleanName, 'Online');

        if (s.has_overlap) {
          const optionsHtml = s.matching_tag_groups.map(g => {
            const t = tagsData[g];
            const tagPreview = t ? ` (${t.ChatTag})` : '';
            return `<option value="${g}" ${s.active_tag_key === g ? 'selected' : ''}>${g}${tagPreview}</option>`;
          }).join('');

          return `
            <div class="staff-card has-overlap" id="staffCard-${s.identity}">
              <div style="flex: 1; min-width: 220px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <span style="font-weight: 600; color: #ffffff; font-size: 0.84rem;">${s.name}</span>
                  <span style="background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 4px; padding: 2px 7px; font-size: 0.68rem; font-weight: 600;">
                    Overlap Detected (${s.groups.join(', ')})
                  </span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; color: var(--text-muted); margin-top: 3px;">
                  SteamID: ${s.identity} &bull; Immunity: ${s.immunity}
                </div>
              </div>
              <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <div>
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 3px;">Choose Active Staff Tag:</div>
                  <select class="form-control" style="height: 30px; font-size: 0.74rem; width: 190px;" onchange="onStaffAssignmentChanged('${s.identity}', this.value)">
                    ${optionsHtml}
                  </select>
                </div>
                <div class="cs2-hud-chat-box" style="padding: 6px 10px; min-width: 160px; height: 32px; display: flex; align-items: center;" id="staffPreview-${s.identity}">
                  <span class="cs2-chat-line">${previewHtml}</span>
                </div>
              </div>
            </div>
          `;
        } else {
          return `
            <div class="staff-card" id="staffCard-${s.identity}">
              <div style="flex: 1; min-width: 220px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <span style="font-weight: 600; color: #ffffff; font-size: 0.84rem;">${s.name}</span>
                  <span class="tag-badge" style="color: #a1a1aa;">${s.groups[0] || 'Default'}</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.70rem; color: var(--text-muted); margin-top: 3px;">
                  SteamID: ${s.identity} &bull; Immunity: ${s.immunity}
                </div>
              </div>
              <div class="cs2-hud-chat-box" style="padding: 6px 10px; min-width: 160px; height: 32px; display: flex; align-items: center;">
                <span class="cs2-chat-line">${previewHtml}</span>
              </div>
            </div>
          `;
        }
      }).join('');
    }

    function onStaffAssignmentChanged(identity, chosenGroup) {
      staffAssignments[identity] = chosenGroup;
      const staffMember = staffData.find(s => s.identity === identity);
      if (staffMember) {
        staffMember.active_tag_key = chosenGroup;
        const activeTag = tagsData[chosenGroup] || { ChatTag: '', NameColor: '{White}', ChatColor: '{White}' };
        const cleanName = staffMember.name.split(' / ')[0];
        const previewEl = document.getElementById(`staffPreview-${identity}`);
        if (previewEl) {
          previewEl.innerHTML = `<span class="cs2-chat-line">${renderCs2ChatLine(false, 'all', activeTag.ChatTag, activeTag.NameColor, activeTag.ChatColor, cleanName, 'Online')}</span>`;
        }
      }
      renderChatSimulation();
      showToast(`Selected "${chosenGroup}" as active tag for staff member.`, 'info');
    }

    function renderTagsTable() {
      const tbody = document.getElementById('tagsTableBody');
      if (!tbody) return;
      tbody.innerHTML = '';

      for (const [k, tag] of Object.entries(tagsData)) {
        const safeKey = k.replace(/[^a-zA-Z0-9]/g, '_');
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--card-border)';
        const isDefault = (k === 'Default');

        const liveRender = renderCs2ChatLine(false, 'all', tag.ChatTag, tag.NameColor, tag.ChatColor, 'Player', 'Example text');

        tr.innerHTML = `
          <td style="padding: 8px 10px; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #fff;">
            ${k}
          </td>
          <td style="padding: 8px 10px;">
            <input type="text" value="${tag.ChatTag || ''}" class="form-control" style="width: 140px; height: 28px; font-size: 0.74rem;" 
              onfocus="lastActiveColorInput = this" oninput="onTagFieldChanged('${k}', 'ChatTag', this.value)">
          </td>
          <td style="padding: 8px 10px;">
            <input type="text" value="${tag.NameColor || ''}" class="form-control" style="width: 110px; height: 28px; font-size: 0.74rem;" 
              onfocus="lastActiveColorInput = this" oninput="onTagFieldChanged('${k}', 'NameColor', this.value)">
          </td>
          <td style="padding: 8px 10px;">
            <input type="text" value="${tag.ChatColor || ''}" class="form-control" style="width: 110px; height: 28px; font-size: 0.74rem;" 
              onfocus="lastActiveColorInput = this" oninput="onTagFieldChanged('${k}', 'ChatColor', this.value)">
          </td>
          <td style="padding: 8px 10px;">
            <div class="cs2-chat-line" id="tagRowPreview-${safeKey}">${liveRender}</div>
          </td>
          <td style="padding: 8px 10px; text-align: right;">
            ${isDefault ? '<span style="font-size: 0.70rem; color: var(--text-muted);">Default</span>' : `<button class="btn btn-sm btn-danger" onclick="deleteChatTag('${k}')">Delete</button>`}
          </td>
        `;
        tbody.appendChild(tr);
      }
    }

    function onTagFieldChanged(key, field, value) {
      if (!tagsData[key]) tagsData[key] = {};
      tagsData[key][field] = value;

      const safeKey = key.replace(/[^a-zA-Z0-9]/g, '_');
      const previewEl = document.getElementById(`tagRowPreview-${safeKey}`);
      if (previewEl) {
        const tag = tagsData[key];
        previewEl.innerHTML = renderCs2ChatLine(false, 'all', tag.ChatTag, tag.NameColor, tag.ChatColor, 'Player', 'Example text');
      }

      renderStaffList();
      renderChatSimulation();
      updateSandboxPreview();
    }

    function renderChatTagColorPalette() {
      const container = document.getElementById('chatTagColorPalette');
      if (!container) return;
      container.innerHTML = TAG_COLOR_PALETTE.map(c => `
        <div class="color-chip" onclick="insertColorTag('${c.tag}')" title="Insert ${c.tag}">
          <span class="color-chip-swatch" style="background: ${c.hex};"></span>
          <span>${c.tag}</span>
        </div>
      `).join('');
    }

    function insertColorTag(tag) {
      if (lastActiveColorInput) {
        lastActiveColorInput.value += tag;
        lastActiveColorInput.dispatchEvent(new Event('input'));
        lastActiveColorInput.focus();
        showToast(`Inserted ${tag}`, 'info');
      } else {
        showToast('Click an input first, then click a color pill.', 'info');
      }
    }

    async function saveAllTagsAndStaff() {
      log('Saving chat tags and staff assignments to VPS...');
      showToast('Saving and hot-reloading tags...', 'info');
      try {
        const res = await fetch('/api/tags/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tags: tagsData, staff_assignments: staffAssignments })
        });
        const out = await res.json();
        if (out.success) {
          log('[OK] ' + (out.message || 'Tags saved.'));
          showToast('Chat tags & staff assignments saved and reloaded in CS2!', 'success');
          loadTagsAndStaff();
        } else {
          log('[ERROR] Failed to save tags: ' + out.error);
          showToast('Save error: ' + out.error, 'error');
        }
      } catch (e) {
        log('[ERROR] Network error saving tags: ' + e);
        showToast('Network error: ' + e, 'error');
      }
    }

    function openAddTagModal() {
      document.getElementById('newTagKeyInput').value = '';
      document.getElementById('newTagTextInput').value = '{Gold}[VIP]';
      document.getElementById('newTagNameColorInput').value = '{Gold}';
      document.getElementById('newTagChatColorInput').value = '{White}';
      updateNewTagModalPreview();
      document.getElementById('addTagModal').classList.add('active');
      document.getElementById('newTagKeyInput').focus();
    }

    function closeAddTagModal() {
      document.getElementById('addTagModal').classList.remove('active');
    }

    function updateNewTagModalPreview() {
      const tagText = document.getElementById('newTagTextInput')?.value || '';
      const nameColor = document.getElementById('newTagNameColorInput')?.value || '{White}';
      const chatColor = document.getElementById('newTagChatColorInput')?.value || '{White}';
      const previewEl = document.getElementById('newTagModalPreview');
      if (previewEl) {
        previewEl.innerHTML = `<span class="cs2-chat-line">${renderCs2ChatLine(false, 'all', tagText, nameColor, chatColor, 'PlayerVIP', 'Hello server!')}</span>`;
      }
    }

    async function submitAddCustomTag() {
      const key = document.getElementById('newTagKeyInput').value.trim();
      const chatTag = document.getElementById('newTagTextInput').value.trim();
      const nameColor = document.getElementById('newTagNameColorInput').value.trim() || '{White}';
      const chatColor = document.getElementById('newTagChatColorInput').value.trim() || '{White}';

      if (!key) {
        showToast('Please specify a role key or SteamID.', 'error');
        return;
      }
      if (!chatTag) {
        showToast('Please enter the tag text (e.g. {Gold}[VIP]).', 'error');
        return;
      }

      tagsData[key] = {
        ChatTag: chatTag,
        NameColor: nameColor,
        ChatColor: chatColor
      };

      closeAddTagModal();
      await saveAllTagsAndStaff();
    }

    function deleteChatTag(key) {
      openConfirmModal(
        'Delete Chat Tag',
        `Are you sure you want to remove the chat tag for "${key}"?`,
        async () => {
          log(`Deleting tag: ${key}...`);
          try {
            const res = await fetch('/api/tags/delete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ key: key })
            });
            const out = await res.json();
            if (out.success) {
              showToast(`Tag "${key}" removed.`, 'success');
              log(`[OK] Deleted tag ${key}`);
              loadTagsAndStaff();
            } else {
              showToast(`Error deleting tag: ${out.error}`, 'error');
            }
          } catch (e) {
            showToast('Delete error: ' + e, 'error');
          }
        },
        'Delete Tag',
        true
      );
    }

    function parseCs2Colors(text) {
      let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      for (const [tag, hex] of Object.entries(CS2_COLORS)) {
        html = html.split(tag).join(`</span><span style="color:${hex};">`);
      }
      return `<span>${html}</span>`;
    }

    // Announcements state
    let announcementsData = {
      IntervalSeconds: 90,
      RandomOrder: true,
      Prefix: "{Gold}[Walliez]{Default}",
      Messages: []
    };

    async function loadAnnouncements() {
      log('Fetching announcements configuration from VPS...');
      try {
        const res = await fetch('/api/announcements');
        announcementsData = await res.json();
        document.getElementById('announcerInterval').value = announcementsData.IntervalSeconds || 90;
        document.getElementById('announcerRandom').value = announcementsData.RandomOrder ? "true" : "false";
        document.getElementById('announcerPrefix').value = announcementsData.Prefix || "{Gold}[Walliez]{Default}";
        renderAnnouncementsList();
        log('Announcements loaded successfully.');
      } catch (e) {
        log('[ERROR] Error loading announcements: ' + e);
      }
    }

    function renderAnnouncementsList() {
      const container = document.getElementById('announcementsList');
      container.innerHTML = '';
      if (!announcementsData.Messages || announcementsData.Messages.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem;">No messages currently configured.</div>';
        updateChatPreview();
        return;
      }
      announcementsData.Messages.forEach((msg, idx) => {
        const item = document.createElement('div');
        item.className = 'msg-item';
        item.innerHTML = `
          <div class="msg-text-box">
            <span style="color:#71717a; font-weight:700; margin-right:8px;">#${idx+1}</span>
            <span>${msg}</span>
          </div>
          <div class="msg-actions">
            <button class="btn btn-sm btn-secondary" onclick="openAnnouncementModal(${idx})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="deleteMessage(${idx})">Delete</button>
          </div>
        `;
        container.appendChild(item);
      });
      updateChatPreview();
    }

    function updateChatPreview() {
      const prefix = document.getElementById('announcerPrefix').value || '';
      const firstMsg = announcementsData.Messages && announcementsData.Messages.length > 0 ? announcementsData.Messages[0] : 'No announcement message selected.';
      const fullText = (prefix ? prefix + ' ' : '') + firstMsg;
      document.getElementById('cs2ChatSimPreview').innerHTML = parseCs2Colors(fullText);
    }

    function insertColorTag(tag) {
      const prefixInput = document.getElementById('announcerPrefix');
      prefixInput.value += tag;
      updateChatPreview();
    }

    function addNewMessagePrompt() {
      openAnnouncementModal(-1);
    }

    function editMessagePrompt(idx) {
      openAnnouncementModal(idx);
    }

    function deleteMessage(idx) {
      openConfirmModal(
        'Delete Announcement',
        `Are you sure you want to delete announcement message #${idx + 1}?`,
        () => {
          announcementsData.Messages.splice(idx, 1);
          renderAnnouncementsList();
          log(`Deleted announcement #${idx + 1}`);
          showToast('Message deleted. Click "Save & Deploy Live" to apply.', 'info');
        },
        'Delete Message',
        true
      );
    }

    async function saveAnnouncementsToServer() {
      log('Saving announcements to server and hot-reloading plugin...');
      announcementsData.IntervalSeconds = parseInt(document.getElementById('announcerInterval').value) || 90;
      announcementsData.RandomOrder = document.getElementById('announcerRandom').value === "true";
      announcementsData.Prefix = document.getElementById('announcerPrefix').value;

      try {
        const res = await fetch('/api/announcements', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(announcementsData)
        });
        const out = await res.json();
        if (out.success) {
          log('[OK] Announcements saved and ServerAnnouncer hot-reloaded via RCON.');
          showToast('Announcements successfully deployed live to server.', 'success');
        } else {
          log('[ERROR] Error saving announcements: ' + out.error);
          showToast('Error saving announcements: ' + out.error, 'error');
        }
      } catch (e) {
        log('[ERROR] Request failed: ' + e);
        showToast('Request failed: ' + e, 'error');
      }
    }

    // Hostname Management
    async function loadHostname() {
      log('Querying current hostname from server...');
      try {
        const res = await fetch('/api/hostname');
        const data = await res.json();
        document.getElementById('serverHostnameInput').value = data.hostname || '';
        updateHostnamePreview();
        log(`Server Hostname: "${data.hostname}"`);
      } catch (e) {
        log('[ERROR] Error querying hostname: ' + e);
      }
    }

    function updateHostnamePreview() {
      const name = document.getElementById('serverHostnameInput').value || 'Counter-Strike 2 Server';
      document.getElementById('hostnamePreviewText').innerText = name;
    }

    async function saveHostname() {
      const name = document.getElementById('serverHostnameInput').value;
      if (!name) return showToast('Hostname cannot be empty.', 'error');
      log(`Applying hostname: "${name}"...`);
      try {
        const res = await fetch('/api/hostname', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({hostname: name})
        });
        const out = await res.json();
        if (out.success) {
          log('[OK] Hostname updated immediately in live server & server.cfg.');
          showToast('Hostname applied live to server & server.cfg.', 'success');
        } else {
          log('[ERROR] Error: ' + out.error);
          showToast('Error: ' + out.error, 'error');
        }
      } catch (e) {
        log('[ERROR] Request failed: ' + e);
        showToast('Request failed: ' + e, 'error');
      }
    }

    // Convars
    let currentConvars = [];
    async function loadConvars() {
      log('Loading server convars...');
      try {
        const res = await fetch('/api/convars');
        currentConvars = await res.json();
        renderConvars(currentConvars);
        log(`Loaded ${currentConvars.length} convars.`);
      } catch (e) {
        log('[ERROR] Error loading convars: ' + e);
      }
    }

    function renderConvars(convars) {
      const grid = document.getElementById('convarsGrid');
      grid.innerHTML = '';
      convars.forEach(item => {
        const row = document.createElement('div');
        row.className = 'convar-row';
        row.innerHTML = `
          <div class="convar-meta">
            <div class="convar-name">${item.name}</div>
            <div class="convar-desc">${item.desc}</div>
          </div>
          <input type="text" class="convar-input" id="cv_${item.name}" value="${item.value}">
        `;
        grid.appendChild(row);
      });
    }

    function filterConvars() {
      const q = document.getElementById('convarSearch').value.toLowerCase();
      const filtered = currentConvars.filter(c => c.name.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q));
      renderConvars(filtered);
    }

    async function saveConvars() {
      log('Applying convar changes via RCON and updating config files...');
      const updates = {};
      currentConvars.forEach(c => {
        const input = document.getElementById(`cv_${c.name}`);
        if (input) updates[c.name] = input.value;
      });
      try {
        const res = await fetch('/api/convars', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(updates)
        });
        const out = await res.json();
        log('[OK] Convars applied successfully via RCON.');
        showToast('Convar settings applied live on the server.', 'success');
      } catch (e) {
        log('[ERROR] Error applying convars: ' + e);
        showToast('Error applying convars: ' + e, 'error');
      }
    }

    // Service Actions
    function serviceAction(action) {
      const actionNames = {
        'restart_cs2': 'Restart CS2 Game Server',
        'restart_bot': 'Restart Discord 24/7 Bot',
        'reload_plugins': 'Reload All CSS Plugins'
      };
      const title = actionNames[action] || action;
      openConfirmModal(
        title,
        `Are you sure you want to execute "${title}"?`,
        async () => {
          log(`Triggering action: ${action}...`);
          try {
            const res = await fetch('/api/service/action', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({action: action})
            });
            const out = await res.json();
            log(`Result: ${out.output || out.status}`);
            showToast(`Action "${title}" completed.`, 'success');
            refreshServices();
          } catch (e) {
            log('[ERROR] Action error: ' + e);
            showToast('Action error: ' + e, 'error');
          }
        },
        title,
        action === 'restart_cs2'
      );
    }

    async function refreshServices() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        const headerStatusText = document.getElementById('headerStatusText');
        const dot = document.querySelector('#headerStatusBadge .status-dot');
        if (headerStatusText) {
          headerStatusText.innerText = data.online ? `Online (${data.players}/${data.max_players})` : 'Offline';
        }
        if (dot) {
          dot.style.background = data.online ? '#22c55e' : '#ef4444';
          dot.style.boxShadow = data.online ? '0 0 8px rgba(34, 197, 94, 0.7)' : '0 0 8px rgba(239, 68, 68, 0.7)';
        }
        const statCs2 = document.getElementById('statCs2Status');
        if (statCs2) {
          statCs2.innerText = data.online ? `Active (${data.map})` : 'Stopped';
          statCs2.style.color = data.online ? '#22c55e' : '#ef4444';
        }
      } catch (e) {
        console.error('refreshServices error:', e);
      }
    }

    async function triggerClientSync() {
      log('Running client anthem sync...');
      showToast('Syncing anthems to local CS2...', 'info');
      try {
        const res = await fetch('/api/sync_client', { method: 'POST' });
        const out = await res.json();
        log(out.output || 'Sync completed.');
        showToast('Local CS2 client sync finished.', 'success');
      } catch (e) {
        log('[ERROR] Sync error: ' + e);
        showToast('Sync error: ' + e, 'error');
      }
    }

    async function launchVisualStudio() {
      log('Launching Visual MVP Web Studio...');
      try {
        const res = await fetch('/api/launch_visual_studio', { method: 'POST' });
        const out = await res.json();
        log(out.message || 'Visual MVP Studio launched.');
        showToast('Visual MVP Web Studio started on port 5500.', 'info');
      } catch (e) {
        log('[ERROR] Error launching studio: ' + e);
        showToast('Error launching studio: ' + e, 'error');
      }
    }

    function triggerWorkshopRebuild() {
      openConfirmModal(
        'Rebuild Workshop Addon',
        'Rebuild all staged anthems, compile to vsnd_c, and deploy VPK to server? (This takes 20-40 seconds)',
        async () => {
          log('Building and compiling Workshop Addon wlzMVP... (this may take 20-40s)');
          showToast('Rebuilding workshop addon in background...', 'info');
          try {
            const res = await fetch('/api/rebuild_workshop', { method: 'POST' });
            const out = await res.json();
            log(out.output || 'Rebuild complete.');
            showToast('Workshop Addon rebuilt and deployed to server.', 'success');
          } catch (e) {
            log('[ERROR] Error rebuilding addon: ' + e);
            showToast('Error rebuilding addon: ' + e, 'error');
          }
        },
        'Rebuild Addon',
        false
      );
    }

    async function launchWorkshopTools() {
      log('Launching Counter-Strike 2 Workshop Tools for wlzMVP...');
      try {
        const res = await fetch('/api/launch_workshop_tools', { method: 'POST' });
        const out = await res.json();
        if (out.success) {
          log(out.message || 'CS2 Tools started.');
          showToast('CS2 Workshop Tools launched successfully.', 'success');
        } else {
          log('[ERROR] Failed starting CS2 tools: ' + (out.error || 'Unknown'));
          showToast('Failed to start CS2 tools: ' + (out.error || 'Unknown'), 'error');
        }
      } catch (e) {
        log('[ERROR] Error starting CS2 tools: ' + e);
        showToast('Error starting tools: ' + e, 'error');
      }
    }

    function openFileConverterPrompt() {
      openConvertModal();
    }

    // All-in-One MVP Pipeline Definition
    const PIPELINE_STEPS = [
      { id: 1, title: 'Trim & Master All Audio Tracks (PCM WAV)', desc: 'Masters all queued tracks to custom durations with 1.0s fadeout at 44.1kHz 16-bit PCM WAV' },
      { id: 2, title: 'Generate Soundevents KV3 Definition', desc: 'Registers all CustomMVP.{id} entries in soundevents_addon.vsndevts for Source 2 audio' },
      { id: 3, title: 'Compile Assets with resourcecompiler.exe', desc: 'Compiles audio to binary .vsnd_c and soundevents to .vsndevts_c for all tracks' },
      { id: 4, title: 'Register in Server MVP_Settings.json', desc: 'Registers kits in server database with custom Message_Center_Bottom_InSecs durations' },
      { id: 5, title: 'Pack & Deploy Workshop VPK Cache', desc: 'Builds Valve VPK with all assets and synchronizes to server linux workshop directories' },
      { id: 6, title: 'Synchronize Local CS2 Game Files', desc: 'Syncs all compiled anthems into your local Steam Counter-Strike 2 directory' },
      { id: 7, title: 'Ready for Workshop Pack Update', desc: 'Addon pack wlzMVP is fully built and ready to be pushed to Steam' }
    ];

    function initPipelineStepsUI() {
      const container = document.getElementById('pipelineStepsList');
      if (!container) return;
      container.innerHTML = PIPELINE_STEPS.map(s => `
        <div class="pipeline-step-item" id="stepItem-${s.id}">
          <div style="display: flex; align-items: center; gap: 4px;">
            <div class="pipeline-step-idx">${s.id}</div>
            <div>
              <div class="pipeline-step-title">${s.title}</div>
              <div class="pipeline-step-desc" id="stepDesc-${s.id}">${s.desc}</div>
            </div>
          </div>
          <div class="pipeline-step-badge" id="stepBadge-${s.id}">Pending</div>
        </div>
      `).join('');
    }

    function updatePipelineStep(stepId, status, msg) {
      const item = document.getElementById(`stepItem-${stepId}`);
      const badge = document.getElementById(`stepBadge-${stepId}`);
      const desc = document.getElementById(`stepDesc-${stepId}`);
      if (!item || !badge) return;

      item.className = `pipeline-step-item ${status}`;
      if (status === 'running') {
        badge.innerText = 'Running...';
        if (msg) desc.innerText = msg;
      } else if (status === 'completed') {
        badge.innerText = 'Completed';
        if (msg) desc.innerText = msg;
      } else if (status === 'failed') {
        badge.innerText = 'Failed';
        if (msg) desc.innerText = msg;
      }
    }

    // =========================================================================
    // MVP BATCH QUEUE & MINIMALIST VINYL AUDIO ENGINE
    // =========================================================================
    let mvpQueue = [];
    let activeAudioTrackId = null;
    let previewCutTimer = null;

    function formatTimeDisplay(secs) {
      if (isNaN(secs) || secs < 0) secs = 0;
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      const ds = Math.floor((secs % 1) * 10);
      return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${ds}`;
    }

    function parseTimeSeconds(timeStr) {
      if (!timeStr) return 0;
      const parts = timeStr.toString().trim().split(':');
      if (parts.length === 3) {
        return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2]);
      } else if (parts.length === 2) {
        return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
      }
      return parseFloat(timeStr) || 0;
    }

    function formatSecondsToTimestamp(secs) {
      const s = Math.floor(secs);
      const m = Math.floor(s / 60);
      const remS = s % 60;
      return `00:${String(m).padStart(2, '0')}:${String(remS).padStart(2, '0')}`;
    }

    function sanitizeIdString(text) {
      return (text || '').toLowerCase().replace(/[^a-z0-9_]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'custom_mvp';
    }

    function createQueueTrack(audioPath = '') {
      const id = 'trk_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
      const cleanPath = (audioPath || '').trim().replace(/^["']|["']$/g, '');
      const parts = cleanPath.split(String.fromCharCode(92)).join('/').split('/');
      const filename = parts[parts.length - 1];
      const dotIdx = filename.lastIndexOf('.');
      const baseName = dotIdx !== -1 ? filename.substring(0, dotIdx) : filename;
      const formattedName = baseName ? baseName.replace(/[_-]/g, ' ').split(' ').map(w => w ? w.charAt(0).toUpperCase() + w.slice(1) : '').join(' ') : 'New MVP Anthem';
      const cleanId = sanitizeIdString(baseName || 'mvp_track');

      return {
        id: id,
        audio_path: cleanPath,
        display_name: formattedName,
        clean_id: cleanId,
        start_time: '00:00:00',
        start_seconds: 0,
        duration: 10.0,
        audio_duration: 180.0, // default until loaded
        volume: parseFloat(localStorage.getItem('cs2_mvp_preview_vol') || '0.8'),
        previous_volume: 0.8,
        audio_element: null,
        is_playing: false,
        is_preview_cut: false,
        bars: generateProceduralWaveBars(64)
      };
    }

    function generateProceduralWaveBars(count) {
      const bars = [];
      for (let i = 0; i < count; i++) {
        // Natural audio envelope pattern (intro, builds up, energetic drops)
        const envelope = Math.sin((i / count) * Math.PI);
        const rand = 0.35 + Math.random() * 0.65;
        const h = Math.max(15, Math.min(100, Math.round(envelope * rand * 100)));
        bars.push(h);
      }
      return bars;
    }

    async function browseMvpMultipleFiles() {
      try {
        const res = await fetch('/api/browse_audio_files', { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.paths && data.paths.length > 0) {
          data.paths.forEach(p => {
            mvpQueue.push(createQueueTrack(p));
          });
          renderMvpQueue();
          showToast(`Added ${data.paths.length} audio file(s) to MVP queue.`, 'info');
          return;
        } else if (data.path) {
          mvpQueue.push(createQueueTrack(data.path));
          renderMvpQueue();
          showToast('Added 1 audio file to MVP queue.', 'info');
          return;
        }
      } catch (e) {
        // Fallback to browser file input if local Python server is unreachable or offline
        let fileInput = document.getElementById('mvpBrowserFallbackInput');
        if (!fileInput) {
          fileInput = document.createElement('input');
          fileInput.id = 'mvpBrowserFallbackInput';
          fileInput.type = 'file';
          fileInput.multiple = true;
          fileInput.accept = '.mp3,.wav,.ogg,.flac,.m4a,.aac,.wma';
          fileInput.style.display = 'none';
          fileInput.onchange = (evt) => {
            const files = Array.from(evt.target.files || []);
            if (files.length > 0) {
              files.forEach(f => {
                mvpQueue.push(createQueueTrack(f.name));
              });
              renderMvpQueue();
              showToast(`Added ${files.length} audio track(s). Verify file path on Windows.`, 'info');
            }
          };
          document.body.appendChild(fileInput);
        }
        fileInput.click();
      }
    }

    function addBlankTrackToQueue() {
      mvpQueue.push(createQueueTrack(''));
      renderMvpQueue();
    }

    function clearMvpQueue() {
      stopAllAudioPlayback();
      mvpQueue = [];
      renderMvpQueue();
    }

    function removeQueueTrack(id) {
      stopAllAudioPlayback();
      mvpQueue = mvpQueue.filter(t => t.id !== id);
      renderMvpQueue();
    }

    function updateTrackField(id, field, value) {
      const track = mvpQueue.find(t => t.id === id);
      if (!track) return;
      track[field] = value;
      if (field === 'audio_path') {
        const parts = value.trim().split(String.fromCharCode(92)).join('/').split('/');
        const filename = parts[parts.length - 1];
        const dotIdx = filename.lastIndexOf('.');
        const base = dotIdx !== -1 ? filename.substring(0, dotIdx) : filename;
        if (!track.display_name || track.display_name === 'New MVP Anthem') {
          track.display_name = base.replace(/[_-]/g, ' ').split(' ').map(w => w ? w.charAt(0).toUpperCase() + w.slice(1) : '').join(' ');
        }
        track.clean_id = sanitizeIdString(base);
        loadAudioForTrack(track);
      }
      if (field === 'display_name') {
        track.clean_id = sanitizeIdString(value);
      }
      renderMvpTrackHeader(track);
    }

    function updateTrackDuration(id, val) {
      const track = mvpQueue.find(t => t.id === id);
      if (!track) return;
      track.duration = parseFloat(val);
      const valEl = document.getElementById(`durVal-${id}`);
      if (valEl) valEl.innerText = `${track.duration.toFixed(1)}s`;
      updateWaveformOverlay(track);
      updateTimeReadout(track);
    }

    function updateTrackStartTime(id, secs) {
      const track = mvpQueue.find(t => t.id === id);
      if (!track) return;
      track.start_seconds = Math.max(0, parseFloat(secs) || 0);
      track.start_time = formatSecondsToTimestamp(track.start_seconds);

      const input = document.getElementById(`startTimeInput-${id}`);
      if (input) input.value = track.start_time;

      const slider = document.getElementById(`scrubberSlider-${id}`);
      if (slider && track.audio_duration > 0) {
        slider.value = track.start_seconds;
      }

      // Seek audio element directly if currently playing so user hears the scrubbed position
      if (track.is_playing && track.audio_element) {
        try {
          track.audio_element.currentTime = track.start_seconds;
        } catch (e) {}
      }

      updateWaveformOverlay(track);
      updateTimeReadout(track);
    }

    function updateTrackVolume(id, val, syncAll = true) {
      const track = mvpQueue.find(t => t.id === id);
      if (!track) return;
      const numVal = Math.max(0, Math.min(100, parseInt(val) || 0));
      track.volume = numVal / 100.0;
      if (track.volume > 0) {
        track.previous_volume = track.volume;
      }

      const valEl = document.getElementById(`volVal-${id}`);
      if (valEl) valEl.innerText = `${numVal}%`;

      const slider = document.getElementById(`volSlider-${id}`);
      if (slider) {
        slider.value = numVal;
        slider.title = `Volume: ${numVal}%`;
      }

      if (track.audio_element && track.is_playing && !track.is_preview_cut) {
        try {
          track.audio_element.volume = track.volume;
        } catch (e) {}
      }

      try {
        localStorage.setItem('cs2_mvp_preview_vol', track.volume.toString());
      } catch (e) {}

      // Keep user's preferred listening level synced across all queued items
      if (syncAll) {
        mvpQueue.forEach(t => {
          if (t.id !== id) {
            t.volume = track.volume;
            if (t.volume > 0) t.previous_volume = t.volume;
            const otherSlider = document.getElementById(`volSlider-${t.id}`);
            if (otherSlider) {
              otherSlider.value = numVal;
              otherSlider.title = `Volume: ${numVal}%`;
            }
            const otherValEl = document.getElementById(`volVal-${t.id}`);
            if (otherValEl) otherValEl.innerText = `${numVal}%`;
          }
        });
      }
    }

    function toggleTrackMute(id) {
      const track = mvpQueue.find(t => t.id === id);
      if (!track) return;
      if (track.volume > 0) {
        track.previous_volume = track.volume;
        updateTrackVolume(id, 0);
      } else {
        const restore = Math.round((track.previous_volume || 0.8) * 100);
        updateTrackVolume(id, restore);
      }
    }

    function setTrackStartPreset(id, presetStr) {
      const secs = parseTimeSeconds(presetStr);
      updateTrackStartTime(id, secs);
    }

    function updateWaveformOverlay(track) {
      const overlay = document.getElementById(`cutOverlay-${track.id}`);
      if (!overlay || track.audio_duration <= 0) return;

      const total = track.audio_duration;
      const leftPct = (track.start_seconds / total) * 100;
      const widthPct = (track.duration / total) * 100;

      overlay.style.left = `${Math.min(100, leftPct)}%`;
      overlay.style.width = `${Math.min(100 - leftPct, widthPct)}%`;

      // Highlight bars inside cut window
      const barContainer = document.getElementById(`waveBars-${track.id}`);
      if (barContainer) {
        const bars = barContainer.querySelectorAll('.mvp-wave-bar');
        const numBars = bars.length;
        bars.forEach((bar, idx) => {
          const barPct = (idx / numBars) * 100;
          if (barPct >= leftPct && barPct <= (leftPct + widthPct)) {
            bar.classList.add('active-slice');
          } else {
            bar.classList.remove('active-slice');
          }
        });
      }
    }

    function updateTimeReadout(track, currentPlayTime = null) {
      const readout = document.getElementById(`timeReadout-${track.id}`);
      if (!readout) return;
      const cur = currentPlayTime !== null ? currentPlayTime : track.start_seconds;
      readout.innerText = `${formatTimeDisplay(cur)} / ${formatTimeDisplay(cur + track.duration)}`;
    }

    function stopAllAudioPlayback() {
      if (previewCutTimer) {
        clearTimeout(previewCutTimer);
        previewCutTimer = null;
      }
      mvpQueue.forEach(t => {
        if (t.audio_element) {
          try {
            t.audio_element.pause();
            t.audio_element.currentTime = t.start_seconds;
          } catch (e) {}
        }
        t.is_playing = false;
        t.is_preview_cut = false;
        setVinylSpinningState(t.id, false);
        updatePlaybackButtonStates(t.id, false);
      });
      activeAudioTrackId = null;
    }

    function setVinylSpinningState(trackId, spinning) {
      const disc = document.getElementById(`vinylDisc-${trackId}`);
      if (disc) {
        if (spinning) disc.classList.add('spinning');
        else disc.classList.remove('spinning');
      }
    }

    function updatePlaybackButtonStates(trackId, isPlaying) {
      const btn = document.getElementById(`btnPlayFull-${trackId}`);
      if (btn) {
        btn.innerHTML = isPlaying ? '⏸ Pause' : '▶ Play Full';
      }
    }

    function loadAudioForTrack(track) {
      if (!track.audio_path) return;
      if (!track.audio_element) {
        track.audio_element = new Audio();
      }
      const streamUrl = `/api/audio_stream?path=${encodeURIComponent(track.audio_path)}`;
      track.audio_element.src = streamUrl;
      track.audio_element.onloadedmetadata = () => {
        if (track.audio_element.duration && !isNaN(track.audio_element.duration)) {
          track.audio_duration = track.audio_element.duration;
          const slider = document.getElementById(`scrubberSlider-${track.id}`);
          if (slider) {
            slider.max = track.audio_duration;
          }
          updateWaveformOverlay(track);
          updateTimeReadout(track);
        }
      };
      track.audio_element.ontimeupdate = () => {
        if (track.is_playing && !track.is_preview_cut) {
          updateTimeReadout(track, track.audio_element.currentTime);
          const slider = document.getElementById(`scrubberSlider-${track.id}`);
          if (slider) slider.value = track.audio_element.currentTime;
        }
      };
      track.audio_element.onended = () => {
        stopAllAudioPlayback();
      };
    }

    function togglePlayMaster(trackId) {
      const track = mvpQueue.find(t => t.id === trackId);
      if (!track || !track.audio_path) {
        showToast('Please select a valid audio file first.', 'error');
        return;
      }

      if (track.is_playing && !track.is_preview_cut) {
        stopAllAudioPlayback();
        return;
      }

      stopAllAudioPlayback();
      loadAudioForTrack(track);

      try {
        track.audio_element.currentTime = track.start_seconds;
        track.audio_element.volume = track.volume !== undefined ? track.volume : 0.8;
        track.audio_element.play().then(() => {
          track.is_playing = true;
          track.is_preview_cut = false;
          activeAudioTrackId = trackId;
          setVinylSpinningState(trackId, true);
          updatePlaybackButtonStates(trackId, true);
        }).catch(err => {
          showToast('Audio playback error: ' + err, 'error');
        });
      } catch (e) {
        showToast('Playback error: ' + e, 'error');
      }
    }

    function previewMvpCut(trackId) {
      const track = mvpQueue.find(t => t.id === trackId);
      if (!track || !track.audio_path) {
        showToast('Please select a valid audio file first.', 'error');
        return;
      }

      stopAllAudioPlayback();
      loadAudioForTrack(track);

      try {
        track.audio_element.currentTime = track.start_seconds;
        const baseVol = track.volume !== undefined ? track.volume : 0.8;
        track.audio_element.volume = baseVol;
        track.audio_element.play().then(() => {
          track.is_playing = true;
          track.is_preview_cut = true;
          activeAudioTrackId = trackId;
          setVinylSpinningState(trackId, true);
          updatePlaybackButtonStates(trackId, true);

          // Simulate in-game 1s audio fadeout at duration - 1s
          const fadeStartMs = Math.max(0, (track.duration - 1.0) * 1000);
          const totalMs = track.duration * 1000;

          // Fadeout timer
          setTimeout(() => {
            if (activeAudioTrackId === trackId && track.is_playing && track.audio_element) {
              let vol = baseVol;
              const fadeSteps = 10;
              const volStep = baseVol / fadeSteps;
              const stepInterval = setInterval(() => {
                vol -= volStep;
                if (vol <= 0 || !track.is_playing) {
                  clearInterval(stepInterval);
                } else if (track.audio_element) {
                  track.audio_element.volume = Math.max(0, vol);
                }
              }, 100);
            }
          }, fadeStartMs);

          // Stop timer
          previewCutTimer = setTimeout(() => {
            if (activeAudioTrackId === trackId) {
              stopAllAudioPlayback();
            }
          }, totalMs);

        }).catch(err => {
          showToast('Audio preview error: ' + err, 'error');
        });
      } catch (e) {
        showToast('Preview error: ' + e, 'error');
      }
    }

    function renderMvpTrackHeader(track) {
      const card = document.getElementById(`trackCard-${track.id}`);
      if (!card) return;
      const hudName = card.querySelector('.hud-track-name');
      if (hudName) hudName.innerText = track.display_name || 'Anthem';
      const eventBadge = card.querySelector('.mvp-pill-event');
      if (eventBadge) eventBadge.innerText = `CustomMVP.${track.clean_id}`;
    }

    function renderMvpQueue() {
      const container = document.getElementById('mvpQueueContainer');
      const countBadge = document.getElementById('mvpQueueCountBadge');
      const summaryTitle = document.getElementById('mvpBatchSummaryTitle');
      const deployBtn = document.getElementById('btnRunMvpBatchPipeline');

      if (!container) return;

      const n = mvpQueue.length;
      if (countBadge) countBadge.innerText = `${n} Track${n === 1 ? '' : 's'}`;
      if (summaryTitle) summaryTitle.innerText = `${n} Anthem${n === 1 ? '' : 's'} Ready to Convert`;
      if (deployBtn) {
        deployBtn.innerText = `Convert & Deploy All to Server (${n} Tracks)`;
        deployBtn.disabled = n === 0;
      }

      if (n === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 36px 20px; border: 1px dashed var(--card-border); border-radius: 8px; background: #020202; margin-bottom: 20px;">
            <div style="font-size: 0.95rem; font-weight: 600; color: #ededed; margin-bottom: 6px;">MVP Queue is Empty</div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 16px;">
              Click "+ Select Audio Files" to choose multiple audio files (.mp3, .wav, .flac) at once, or add a track manually.
            </div>
            <button class="btn btn-sm" style="background:#22c55e; color:#000; font-weight:700;" onclick="browseMvpMultipleFiles()">
              + Select Audio Files
            </button>
          </div>
        `;
        return;
      }

      container.innerHTML = mvpQueue.map(track => `
        <div class="mvp-track-card" id="trackCard-${track.id}">
          <!-- Top Row: Vinyl + Info & Badges + HUD + Time -->
          <div class="mvp-card-top">
            <!-- Vinyl Record Sleeve Widget -->
            <div class="mvp-vinyl-jacket" onclick="togglePlayMaster('${track.id}')" title="Click to Play/Pause">
              <div class="mvp-vinyl-disc" id="vinylDisc-${track.id}">
                <div class="mvp-vinyl-center">
                  <div class="mvp-vinyl-play-icon"></div>
                </div>
              </div>
            </div>

            <!-- Track Info & Controls -->
            <div class="mvp-track-info">
              <div class="mvp-track-badges">
                <span class="mvp-pill mvp-pill-green">★ READY TO CONVERT</span>
                <span class="mvp-pill mvp-pill-subtle">SOURCE 2 VSND • 44.1kHz</span>
                <span class="mvp-pill mvp-pill-event">CustomMVP.${track.clean_id}</span>
              </div>

              <!-- Editable Display Name -->
              <input type="text" class="mvp-title-input" value="${track.display_name}" placeholder="Track Title / Artist - Song"
                     oninput="updateTrackField('${track.id}', 'display_name', this.value)">

              <!-- In-Game Round HUD Preview Box -->
              <div class="mvp-hud-box">
                <span class="mvp-hud-tag">IN-GAME HUD</span>
                <span>★ <strong>doggg</strong> is MVP of the Round! Playing <strong class="hud-track-name" style="color:#fff;">${track.display_name}</strong></span>
              </div>
            </div>

            <!-- Top Right: Readout & Delete -->
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
              <div class="mvp-time-readout" id="timeReadout-${track.id}">
                ${formatTimeDisplay(track.start_seconds)} / ${formatTimeDisplay(track.start_seconds + track.duration)}
              </div>
              <button class="btn btn-sm" style="background:transparent; border:1px solid #27272a; color:#ef4444; font-size:0.7rem; padding:2px 8px;"
                      onclick="removeQueueTrack('${track.id}')">
                Remove
              </button>
            </div>
          </div>

          <!-- Audio File Path Row -->
          <div style="display: flex; gap: 8px; align-items: center;">
            <input type="text" style="font-size: 0.74rem; font-family: 'JetBrains Mono', monospace; padding: 6px 10px; background:#010101;"
                   placeholder="C:\\path\\to\\anthem.mp3" value="${track.audio_path}"
                   onchange="updateTrackField('${track.id}', 'audio_path', this.value)">
            <button class="btn btn-sm btn-secondary" style="white-space:nowrap; padding:6px 12px;"
                    onclick="browseTrackAudioPath('${track.id}')">
              Browse
            </button>
          </div>

          <!-- Waveform Visualizer & Cut Region Scrubber -->
          <div>
            <div class="mvp-waveform-wrap" onclick="onWaveformClicked(event, '${track.id}')">
              <div class="mvp-cut-overlay" id="cutOverlay-${track.id}"></div>
              <div class="mvp-waveform-bars" id="waveBars-${track.id}">
                ${track.bars.map(h => `<div class="mvp-wave-bar" style="height:${h}%;"></div>`).join('')}
              </div>
            </div>

            <!-- Minimal Scrubber Slider (Image 2 style white thumb) -->
            <div class="mvp-slider-track-wrap">
              <input type="range" class="mvp-scrubber-slider" id="scrubberSlider-${track.id}"
                     min="0" max="${track.audio_duration}" step="0.5" value="${track.start_seconds}"
                     oninput="updateTrackStartTime('${track.id}', this.value)">
            </div>
          </div>

          <!-- Bottom Control Bar -->
          <div class="mvp-controls-row">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
              <button class="mvp-btn-playback" id="btnPlayFull-${track.id}" onclick="togglePlayMaster('${track.id}')">
                ▶ Play Full
              </button>
              <button class="mvp-btn-playback" style="background:#111; border-color:#22c55e; color:#22c55e;" onclick="previewMvpCut('${track.id}')">
                ▶ Preview MVP Cut
              </button>

              <!-- Minimal Luxury Volume Slider -->
              <div class="mvp-volume-control" title="Preview playback volume">
                <span class="mvp-vol-btn" onclick="toggleTrackMute('${track.id}')" title="Click to mute/unmute">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>
                </span>
                <input type="range" class="mvp-vol-slider" id="volSlider-${track.id}" min="0" max="100" step="1"
                       value="${Math.round((track.volume !== undefined ? track.volume : 0.8) * 100)}"
                       oninput="updateTrackVolume('${track.id}', this.value)">
                <span class="mvp-vol-val" id="volVal-${track.id}">${Math.round((track.volume !== undefined ? track.volume : 0.8) * 100)}%</span>
              </div>
            </div>

            <!-- Start Time Input & Presets -->
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span style="font-size: 0.72rem; color: var(--text-muted);">Start:</span>
              <input type="text" id="startTimeInput-${track.id}" value="${track.start_time}"
                     style="width: 74px; font-size: 0.74rem; font-family: 'JetBrains Mono', monospace; text-align: center; padding: 4px;"
                     onchange="setTrackStartPreset('${track.id}', this.value)">
              <div class="color-tags-container" style="display:inline-flex; gap:4px; margin:0;">
                <span class="color-tag-pill" style="font-size:0.65rem; padding:2px 6px;" onclick="setTrackStartPreset('${track.id}', '00:00:00')">00:00</span>
                <span class="color-tag-pill" style="font-size:0.65rem; padding:2px 6px;" onclick="setTrackStartPreset('${track.id}', '00:00:30')">00:30</span>
                <span class="color-tag-pill" style="font-size:0.65rem; padding:2px 6px;" onclick="setTrackStartPreset('${track.id}', '00:00:45')">00:45</span>
                <span class="color-tag-pill" style="font-size:0.65rem; padding:2px 6px;" onclick="setTrackStartPreset('${track.id}', '00:01:00')">01:00</span>
              </div>
            </div>

            <!-- MVP Duration Slider (5s to 15s) -->
            <div class="mvp-duration-control">
              <span class="mvp-dur-label">MVP Duration:</span>
              <input type="range" class="mvp-dur-slider" min="5" max="15" step="0.5" value="${track.duration}"
                     oninput="updateTrackDuration('${track.id}', this.value)">
              <span class="mvp-dur-val" id="durVal-${track.id}">${track.duration.toFixed(1)}s</span>
            </div>
          </div>
        </div>
      `).join('');

      // Post-render init: Load audio metadata & initialize overlays
      mvpQueue.forEach(track => {
        loadAudioForTrack(track);
        updateWaveformOverlay(track);
      });
    }

    function onWaveformClicked(e, trackId) {
      const track = mvpQueue.find(t => t.id === trackId);
      if (!track || track.audio_duration <= 0) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, clickX / rect.width));
      const secs = pct * track.audio_duration;
      updateTrackStartTime(trackId, secs);
    }

    async function browseTrackAudioPath(trackId) {
      try {
        const res = await fetch('/api/browse_audio_file', { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (data.path) {
          updateTrackField(trackId, 'audio_path', data.path);
          return;
        }
      } catch (e) {
        let fileInput = document.getElementById('mvpTrackAudioInput-' + trackId);
        if (!fileInput) {
          fileInput = document.createElement('input');
          fileInput.id = 'mvpTrackAudioInput-' + trackId;
          fileInput.type = 'file';
          fileInput.accept = '.mp3,.wav,.ogg,.flac,.m4a,.aac,.wma';
          fileInput.style.display = 'none';
          fileInput.onchange = (evt) => {
            const file = (evt.target.files || [])[0];
            if (file) {
              updateTrackField(trackId, 'audio_path', file.name);
            }
          };
          document.body.appendChild(fileInput);
        }
        fileInput.click();
      }
    }

    // =========================================================================
    // BATCH PIPELINE EXECUTION
    // =========================================================================
    async function runMvpBatchPipeline() {
      if (mvpQueue.length === 0) {
        showToast('Your queue is empty! Add at least 1 track before running the pipeline.', 'error');
        return;
      }

      // Check if all tracks have valid paths
      const invalid = mvpQueue.filter(t => !t.audio_path);
      if (invalid.length > 0) {
        showToast(`Please specify audio files for all ${invalid.length} queue item(s).`, 'error');
        return;
      }

      stopAllAudioPlayback();

      initPipelineStepsUI();
      document.getElementById('mvpPipelineTracker').style.display = 'block';
      document.getElementById('workshopReadyBanner').style.display = 'none';
      document.getElementById('pipelineOverallStatus').innerText = `Processing Batch Pipeline (${mvpQueue.length} Tracks)...`;
      document.getElementById('pipelineOverallStatus').style.color = 'var(--gold)';

      const btn = document.getElementById('btnRunMvpBatchPipeline');
      btn.disabled = true;
      btn.innerText = `Executing Pipeline (${mvpQueue.length} Tracks)...`;

      log(`[MVP BATCH] Starting Pipeline for ${mvpQueue.length} tracks...`);

      const payload = {
        tracks: mvpQueue.map(t => ({
          audio_path: t.audio_path,
          display_name: t.display_name,
          start_time: t.start_time,
          duration: t.duration,
          clean_id: t.clean_id
        }))
      };

      try {
        const res = await fetch('/api/mvp/pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let hasError = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split(String.fromCharCode(10));
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const ev = JSON.parse(line);
              updatePipelineStep(ev.step, ev.status, ev.msg);
              log(`[MVP Step ${ev.step}] ${ev.msg}`);
              if (ev.status === 'failed') {
                hasError = true;
                showToast(`Step ${ev.step} failed: ${ev.msg}`, 'error');
              }
              if (ev.step === 7 && ev.status === 'completed') {
                document.getElementById('workshopReadyBanner').style.display = 'block';
                document.getElementById('pipelineOverallStatus').innerText = 'Ready for Steam Workshop!';
                document.getElementById('pipelineOverallStatus').style.color = '#22c55e';
                showToast(`Batch completed! ${mvpQueue.length} anthem(s) mastered & deployed.`, 'success');
              }
            } catch (err) {}
          }
        }

        if (hasError) {
          document.getElementById('pipelineOverallStatus').innerText = 'Pipeline Encountered Errors';
          document.getElementById('pipelineOverallStatus').style.color = '#ef4444';
        } else {
          loadMvpList();
        }
      } catch (e) {
        log('[MVP BATCH ERROR] Pipeline error: ' + e);
        showToast('Pipeline network error: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerText = `Convert & Deploy All to Server (${mvpQueue.length} Tracks)`;
      }
    }

    async function loadMvpList() {
      const tbody = document.getElementById('mvpAnthemsTableBody');
      if (!tbody) return;
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:18px; color:var(--text-muted);">Loading anthems from server...</td></tr>';

      try {
        const res = await fetch('/api/mvp/list');
        const data = await res.json();
        if (data.anthems && data.anthems.length > 0) {
          tbody.innerHTML = data.anthems.map(a => `
            <tr>
              <td style="padding: 10px 14px; font-weight: 600; color: #fff;">${a.name}</td>
              <td style="padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #38bdf8;">${a.event}</td>
              <td style="padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #22c55e;">${a.duration ? a.duration + 's' : '10s'}</td>
              <td style="padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: var(--text-muted);">${a.path}</td>
              <td style="padding: 10px 14px; text-align: right;">
                <button class="btn btn-sm btn-danger" onclick="deleteMvp('${a.id}', '${encodeURIComponent(a.name)}')">Delete</button>
              </td>
            </tr>
          `).join('');
        } else {
          tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:18px; color:var(--text-muted);">No custom anthems registered yet.</td></tr>';
        }
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:18px; color:#ef4444;">Error loading anthems: ${e}</td></tr>`;
      }
    }

    function deleteMvp(kitId, encodedName) {
      const kitName = decodeURIComponent(encodedName);
      openConfirmModal(
        'Delete MVP Anthem',
        `Remove anthem "${kitName}" from server MVP_Settings.json?`,
        async () => {
          log(`Deleting anthem: ${kitId}...`);
          try {
            const res = await fetch('/api/mvp/delete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ kit_id: kitId })
            });
            const out = await res.json();
            if (out.success) {
              showToast(`Anthem "${kitName}" deleted.`, 'success');
              log(`[OK] Deleted anthem ${kitId}`);
              loadMvpList();
            } else {
              showToast(`Error deleting anthem: ${out.error}`, 'error');
            }
          } catch (e) {
            showToast('Delete error: ' + e, 'error');
          }
        },
        'Delete Anthem',
        true
      );
    }
    // Initial Load
    function initApp() {
      refreshServices();
      loadAnnouncements();
      loadTagsAndStaff();
      loadMvpList();
      setInterval(refreshServices, 10000);
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initApp);
    } else {
      initApp();
    }
    window.onload = () => {
      refreshServices();
    };
  </script>
</body>
</html>
"""

# Common convars list with descriptions
POPULAR_CONVARS = [
    {"name": "mp_roundtime_defuse", "desc": "Round time for defuse maps (minutes)", "default": "1.92"},
    {"name": "mp_roundtime", "desc": "General round time (minutes)", "default": "1.92"},
    {"name": "mp_maxrounds", "desc": "Total match rounds (e.g. 24 for MR12)", "default": "24"},
    {"name": "mp_freezetime", "desc": "Round start freeze time (seconds)", "default": "15"},
    {"name": "mp_buytime", "desc": "Buy time in seconds", "default": "20"},
    {"name": "mp_startmoney", "desc": "Starting cash", "default": "800"},
    {"name": "mp_maxmoney", "desc": "Max cash player can hold", "default": "16000"},
    {"name": "mp_c4timer", "desc": "Bomb explosion timer (seconds)", "default": "40"},
    {"name": "mp_warmuptime", "desc": "Warmup duration (seconds)", "default": "60"},
    {"name": "mp_friendlyfire", "desc": "Friendly fire (1 = on, 0 = off)", "default": "0"},
    {"name": "mp_overtime_enable", "desc": "Enable overtime on tie (1 = on, 0 = off)", "default": "1"},
    {"name": "mp_overtime_maxrounds", "desc": "Rounds per overtime", "default": "6"},
    {"name": "mp_halftime", "desc": "Switch teams at halftime", "default": "1"},
    {"name": "mp_match_can_clinch", "desc": "End match early if win clinched", "default": "1"}
]

class ControlCenterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress noisy request logs

    def do_GET(self):
        if self.path.startswith("/api/audio_stream"):
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                file_path = query.get("path", [""])[0]
                if not file_path or not os.path.exists(file_path):
                    self.send_response(404)
                    self.end_headers()
                    return

                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    ".mp3": "audio/mpeg",
                    ".wav": "audio/wav",
                    ".ogg": "audio/ogg",
                    ".flac": "audio/flac",
                    ".m4a": "audio/mp4",
                    ".aac": "audio/aac",
                }
                content_type = mime_types.get(ext, "application/octet-stream")
                file_size = os.path.getsize(file_path)

                range_header = self.headers.get("Range")
                if range_header and range_header.startswith("bytes="):
                    range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
                    if range_match:
                        start = int(range_match.group(1))
                        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                        end = min(end, file_size - 1)
                        length = end - start + 1

                        self.send_response(206)
                        self.send_header("Content-Type", content_type)
                        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                        self.send_header("Content-Length", str(length))
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()

                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = length
                            while remaining > 0:
                                chunk = f.read(min(remaining, 65536))
                                if not chunk:
                                    break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                        return

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except Exception:
                pass
            return

        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
            return

        if self.path == "/api/status":
            info = a2s_info()
            self.send_json(info)
            return

        if self.path == "/api/announcements":
            try:
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_ANNOUNCER_PATH, 'r') as f:
                    raw = f.read().decode('utf-8')
                sftp.close()
                ssh.close()
                clean_lines = [l for l in raw.splitlines() if not l.strip().startswith("//")]
                data = json.loads("\n".join(clean_lines))
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e), "IntervalSeconds": 90, "RandomOrder": True, "Prefix": "{Gold}★ {LightBlue}[Walliez]{Default}", "Messages": []})
            return

        if self.path == "/api/hostname":
            try:
                info = a2s_info()
                hostname = info.get("name", "")
                if not hostname:
                    ssh = get_ssh_client()
                    _, stdout, _ = ssh.exec_command(f'grep -E "^[[:space:]]*hostname" {REMOTE_SERVER_CFG}')
                    line = stdout.read().decode('utf-8').strip()
                    ssh.close()
                    m = re.search(r'hostname\s+["\'](.*?)["\']', line)
                    hostname = m.group(1) if m else "Counter-Strike 2 Server"
                self.send_json({"hostname": hostname})
            except Exception as e:
                self.send_json({"hostname": "Counter-Strike 2 Server", "error": str(e)})
            return

        if self.path == "/api/convars":
            # Query live convars via RCON
            results = []
            for item in POPULAR_CONVARS:
                val = rcon_exec(item["name"])
                clean_val = item["default"]
                if val:
                    # Parse 'convar = "val"'
                    m = re.search(r'=\s*"?([^\s"]+)"?', val)
                    if m:
                        clean_val = m.group(1)
                results.append({"name": item["name"], "desc": item["desc"], "value": clean_val})
            self.send_json(results)
            return

        if self.path == "/api/tags":
            try:
                payload = get_tags_and_staff_payload()
                self.send_json(payload)
            except Exception as e:
                self.send_json({"success": False, "error": str(e), "tags": {}, "staff": []})
            return

        if self.path == "/api/mvp/list":
            try:
                ssh = get_ssh_client(timeout=10)
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_MVP_SETTINGS, 'r') as f:
                    raw = f.read().decode('utf-8')
                sftp.close()
                ssh.close()
                data = json.loads(raw)
                anthems = []
                for k, v in data.items():
                    anthems.append({
                        "id": k,
                        "name": v.get("MVP_Kit_Name", k),
                        "event": v.get("SoundEvent") or v.get("Sound_Event", ""),
                        "path": v.get("Sound_Path_1", ""),
                        "duration": v.get("Message_Center_Bottom_InSecs", 10)
                    })
                self.send_json({"success": True, "anthems": anthems})
            except Exception as e:
                try:
                    local_f = os.path.join(LOCAL_BACKUP, "MVP_Settings.json")
                    if os.path.exists(local_f):
                        with open(local_f, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        anthems = []
                        for k, v in data.items():
                            anthems.append({
                                "id": k,
                                "name": v.get("MVP_Kit_Name", k),
                                "event": v.get("SoundEvent", ""),
                                "path": v.get("Sound_Path_1", "")
                            })
                        self.send_json({"success": True, "anthems": anthems})
                        return
                except Exception:
                    pass
                self.send_json({"success": False, "error": str(e), "anthems": []})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if self.path == "/api/announcements":
            try:
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_ANNOUNCER_PATH, 'w') as f:
                    json.dump(req_data, f, indent=2)
                sftp.close()
                ssh.close()
                # Reload via RCON
                reload_out = rcon_exec("css_plugins reload ServerAnnouncer")
                self.send_json({"success": True, "rcon": reload_out})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/hostname":
            new_name = req_data.get("hostname", "").strip()
            if not new_name:
                self.send_json({"success": False, "error": "Empty hostname"})
                return
            try:
                # 1. Apply via RCON live
                rcon_exec(f'hostname "{new_name}"')
                # 2. Save in server.cfg permanently
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_SERVER_CFG, 'r') as f:
                    content = f.read().decode('utf-8')
                if re.search(r'^[ \t]*hostname\s+.*$', content, flags=re.MULTILINE):
                    new_content = re.sub(r'^[ \t]*hostname\s+.*$', f'hostname "{new_name}"', content, flags=re.MULTILINE)
                else:
                    new_content = f'hostname "{new_name}"\n' + content
                with sftp.open(REMOTE_SERVER_CFG, 'w') as f:
                    f.write(new_content)
                sftp.close()
                ssh.close()
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/convars":
            try:
                ssh = get_ssh_client()
                for cname, cval in req_data.items():
                    rcon_exec(f'{cname} {cval}')
                    # Also append/update in gamemode_competitive_server.cfg
                    cmd = f'sed -i "/^{cname}/d" {REMOTE_COMP_CFG} && echo "{cname} {cval}" >> {REMOTE_COMP_CFG}'
                    ssh.exec_command(cmd)
                ssh.close()
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/tags/save":
            try:
                new_tags = req_data.get("tags", {})
                staff_assignments = req_data.get("staff_assignments", {})

                ssh = get_ssh_client()
                sftp = ssh.open_sftp()

                with sftp.open(REMOTE_CHATMANAGER_CONFIG, 'r') as f:
                    cm_data = json.loads(f.read().decode('utf-8'))
                cm_data["Tags"] = new_tags
                with sftp.open(REMOTE_CHATMANAGER_CONFIG, 'w') as f:
                    f.write(json.dumps(cm_data, indent=2, ensure_ascii=False))

                if staff_assignments:
                    with sftp.open(REMOTE_ADMINS_CONFIG, 'r') as f:
                        raw_admins = f.read().decode('utf-8').lstrip('\ufeff')
                        admins_data = json.loads(raw_admins)

                    for ident, chosen_group in staff_assignments.items():
                        for entry_key, entry in admins_data.items():
                            if str(entry.get("identity", entry_key)).strip() == ident:
                                cur_groups = entry.get("groups", [])
                                if chosen_group in cur_groups:
                                    cur_groups.remove(chosen_group)
                                    entry["groups"] = [chosen_group] + cur_groups
                                elif chosen_group.startswith("#"):
                                    entry["groups"] = [chosen_group] + [g for g in cur_groups if g != chosen_group]

                    with sftp.open(REMOTE_ADMINS_CONFIG, 'w') as f:
                        f.write(json.dumps(admins_data, indent=2, ensure_ascii=False))

                sftp.close()
                ssh.close()

                rcon_exec("css_admins_reload")
                rcon_exec("css_plugins reload 9")

                self.send_json({"success": True, "message": "Chat tags and staff assignments hot-reloaded successfully."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/tags/delete":
            tag_key = req_data.get("key", "").strip()
            if not tag_key:
                self.send_json({"success": False, "error": "Missing tag key"})
                return
            try:
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_CHATMANAGER_CONFIG, 'r') as f:
                    cm_data = json.loads(f.read().decode('utf-8'))
                if tag_key in cm_data.get("Tags", {}):
                    del cm_data["Tags"][tag_key]
                with sftp.open(REMOTE_CHATMANAGER_CONFIG, 'w') as f:
                    f.write(json.dumps(cm_data, indent=2, ensure_ascii=False))
                sftp.close()
                ssh.close()

                rcon_exec("css_plugins reload 9")
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/service/action":
            action = req_data.get("action")
            ssh = get_ssh_client()
            if action == "restart_cs2":
                _, stdout, _ = ssh.exec_command("systemctl restart cs2 && sleep 2 && systemctl status cs2 --no-pager")
                out = stdout.read().decode('utf-8', errors='replace')
            elif action == "restart_bot":
                _, stdout, _ = ssh.exec_command("systemctl restart cs2-discord-bot && sleep 2 && systemctl status cs2-discord-bot --no-pager")
                out = stdout.read().decode('utf-8', errors='replace')
            elif action == "reload_plugins":
                out = rcon_exec("css_plugins reload")
            else:
                out = "Unknown action"
            ssh.close()
            self.send_json({"success": True, "output": out})
            return

        if self.path == "/api/sync_client":
            try:
                out = sync_local_client_files()
                self.send_json({"success": True, "output": out})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/convert_mp3":
            audio_path = req_data.get("path", "").strip(' "\'')
            if not os.path.exists(audio_path):
                self.send_json({"success": False, "error": "File does not exist on disk."})
                return
            try:
                out = convert_audio_clean_mp3(audio_path)
                self.send_json({"success": True, "output": out})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/rebuild_workshop":
            try:
                out = rebuild_full_workshop_addon()
                self.send_json({"success": True, "output": out})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/launch_workshop_tools":
            try:
                cs2_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
                if os.path.exists(cs2_exe):
                    subprocess.Popen([cs2_exe, "-tools", "-addon", "wlzMVP"])
                    self.send_json({"success": True, "message": "CS2 Workshop Tools launched."})
                else:
                    self.send_json({"success": False, "error": "cs2.exe not found at standard Steam path."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return
        if self.path in ("/api/browse_audio_file", "/api/browse_audio_files"):
            try:
                paths = browse_audio_files(multiple=True)
                self.send_json({
                    "success": True,
                    "paths": paths,
                    "path": paths[0] if paths else ""
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e), "paths": [], "path": ""})
            return

        if self.path == "/api/mvp/delete":
            kit_id = req_data.get("kit_id", "")
            if not kit_id:
                self.send_json({"success": False, "error": "Missing kit_id"})
                return
            try:
                ssh = get_ssh_client(timeout=10)
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_MVP_SETTINGS, 'r') as f:
                    data = json.loads(f.read().decode('utf-8'))
                if kit_id in data:
                    del data[kit_id]
                formatted = json.dumps(data, indent=2, ensure_ascii=False)
                with sftp.open(REMOTE_MVP_SETTINGS, 'w') as f:
                    f.write(formatted)
                sftp.close()
                ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
                ssh.close()

                local_f = os.path.join(LOCAL_BACKUP, "MVP_Settings.json")
                if os.path.exists(local_f):
                    with open(local_f, "w", encoding="utf-8") as f:
                        f.write(formatted)
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/mvp/pipeline":
            tracks_data = req_data.get("tracks")
            if not tracks_data:
                audio_path = req_data.get("audio_path", "").strip(' "\'')
                display_name = req_data.get("display_name", "").strip()
                start_time = req_data.get("start_time", "00:00:00").strip()
                duration = req_data.get("duration", 10.0)
                tracks_data = [{
                    "audio_path": audio_path,
                    "display_name": display_name,
                    "start_time": start_time,
                    "duration": duration
                }]

            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            try:
                for ev in execute_mvp_batch_pipeline(tracks_data):
                    line = json.dumps(ev, ensure_ascii=False) + "\n"
                    self.wfile.write(line.encode('utf-8'))
                    self.wfile.flush()
            except Exception as e:
                err_line = json.dumps({"step": 0, "status": "failed", "msg": f"Pipeline exception: {e}"}) + "\n"
                try:
                    self.wfile.write(err_line.encode('utf-8'))
                    self.wfile.flush()
                except Exception:
                    pass
            return

        self.send_response(404)
        self.end_headers()

    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

def open_app_window(url):
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.path.exists(edge_path):
        try:
            subprocess.Popen([edge_path, f"--app={url}"])
            return
        except Exception:
            pass
    webbrowser.open(url)

def main():
    port = 5890
    url = f"http://127.0.0.1:{port}"
    server = None
    try:
        server = HTTPServer(("127.0.0.1", port), ControlCenterHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
    except OSError:
        print(f"[*] Port {port} already listening. Re-using active server instance.")

    print("=" * 65)
    print("        CS2 Server Control Center (Active)")
    print("=" * 65)
    print(f"[*] Server Control Center running at: {url}")
    print("[*] Launching native standalone application window...")

    launched_standalone = False
    if "--daemon" not in sys.argv and "--server-only" not in sys.argv and "--no-gui" not in sys.argv:
        try:
            import webview
            window = webview.create_window(
                'CS2 Server Control Center',
                url,
                width=1180,
                height=860,
                min_size=(900, 600),
                background_color='#000000'
            )
            launched_standalone = True
            webview.start()
        except Exception as e:
            print(f"[!] Native window error: {e}")
            launched_standalone = False

    if not launched_standalone:
        if "--daemon" not in sys.argv and "--server-only" not in sys.argv:
            open_app_window(url)
            print("[*] Standalone GUI unavailable. Opened browser fallback.")
        else:
            print(f"[*] Background server daemon active at {url}")
        print("[*] Press Ctrl+C in this terminal window to stop the server.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    if server:
        try:
            server.shutdown()
        except Exception:
            pass
    print("\n[*] Control Center closed gracefully.")

if __name__ == "__main__":
    main()

