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

def browse_audio_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            title="Select Audio File for MVP Anthem",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma"),
                ("All Files", "*.*")
            ]
        )
        root.destroy()
        return path or ""
    except Exception:
        return ""

def execute_mvp_pipeline(audio_path, display_name, start_time="00:00:00"):
    import tempfile
    import vpk

    if not audio_path or not os.path.exists(audio_path):
        yield {"step": 1, "status": "failed", "msg": f"Audio file not found: '{audio_path}'"}
        return

    clean_id = sanitize_id(os.path.splitext(os.path.basename(audio_path))[0])
    if not display_name or not display_name.strip():
        display_name = os.path.splitext(os.path.basename(audio_path))[0].replace("_", " ").title()
    fmt_start = format_start_time(start_time)

    # STEP 1: Trim & Master Audio (10s, 1s fadeout, 44.1kHz PCM WAV)
    yield {"step": 1, "status": "running", "msg": f"Mastering '{os.path.basename(audio_path)}' from {fmt_start} (10s with 1s fadeout)..."}
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

    dest_wav = os.path.join(CONTENT_DIR, "sounds", "mvp", f"{clean_id}.wav")
    backup_wav = os.path.join(LOCAL_BACKUP, "sounds", "mvp", f"{clean_id}.wav")

    ffmpeg_local = find_ffmpeg()
    converted_ok = False

    if ffmpeg_local and os.path.exists(ffmpeg_local):
        try:
            cmd = [
                ffmpeg_local, "-y", "-ss", fmt_start, "-i", audio_path,
                "-t", "10", "-af", "afade=t=out:st=9:d=1",
                "-c:a", "pcm_s16le", "-ar", "44100", dest_wav
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            shutil.copy2(dest_wav, backup_wav)
            converted_ok = True
        except Exception:
            converted_ok = False

    if not converted_ok:
        try:
            ssh = get_ssh_client(timeout=15)
            sftp = ssh.open_sftp()
            rem_in = f"/tmp/mvp_in_{clean_id}.tmp"
            rem_wav = f"/tmp/mvp_out_{clean_id}.wav"
            sftp.put(audio_path, rem_in)
            cmd = f"/usr/local/bin/ffmpeg -y -ss {fmt_start} -i {rem_in} -t 10 -af 'afade=t=out:st=9:d=1' -c:a pcm_s16le -ar 44100 {rem_wav}"
            _, stdout, _ = ssh.exec_command(cmd)
            stdout.channel.recv_exit_status()
            sftp.get(rem_wav, dest_wav)
            sftp.close()
            ssh.exec_command(f"rm -f {rem_in} {rem_wav}")
            ssh.close()
            shutil.copy2(dest_wav, backup_wav)
            converted_ok = True
        except Exception as e:
            yield {"step": 1, "status": "failed", "msg": f"Audio mastering failed: {e}"}
            return

    wav_size = os.path.getsize(dest_wav) if os.path.exists(dest_wav) else 0
    yield {"step": 1, "status": "completed", "msg": f"Mastered 10.0s WAV created: {wav_size:,} bytes"}

    # STEP 2: Generate / Update KV3 soundevents_addon.vsndevts
    yield {"step": 2, "status": "running", "msg": "Generating KV3 soundevents definitions..."}
    try:
        local_mvp_dir = os.path.join(LOCAL_BACKUP, "sounds", "mvp")
        all_tracks = []
        if os.path.exists(local_mvp_dir):
            for f in os.listdir(local_mvp_dir):
                if f.lower().endswith(".wav"):
                    k = sanitize_id(os.path.splitext(f)[0])
                    if k not in all_tracks:
                        all_tracks.append(k)
        if clean_id not in all_tracks:
            all_tracks.append(clean_id)

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

        yield {"step": 2, "status": "completed", "msg": f"KV3 definitions updated ({len(all_tracks)} tracks registered)"}
    except Exception as e:
        yield {"step": 2, "status": "failed", "msg": f"Soundevents generation failed: {e}"}
        return

    # STEP 3: Compile Source 2 Assets with resourcecompiler.exe
    yield {"step": 3, "status": "running", "msg": "Compiling binary .vsnd_c and .vsndevts_c assets..."}
    try:
        cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        expected_vsnd = os.path.join(GAME_DIR, "sounds", "mvp", f"{clean_id}.vsnd_c")
        if os.path.exists(expected_vsnd):
            yield {"step": 3, "status": "completed", "msg": f"Compiled asset created: {clean_id}.vsnd_c ({os.path.getsize(expected_vsnd):,} bytes)"}
        else:
            yield {"step": 3, "status": "completed", "msg": "Resource compilation completed successfully"}
    except Exception as e:
        yield {"step": 3, "status": "failed", "msg": f"Resource compilation failed: {e}"}
        return

    # STEP 4: Register in Server MVP_Settings.json & Local Backup
    yield {"step": 4, "status": "running", "msg": "Registering kit in server MVP_Settings.json..."}
    try:
        ssh = get_ssh_client(timeout=15)
        sftp = ssh.open_sftp()
        server_mvp_data = {}
        try:
            with sftp.open(REMOTE_MVP_SETTINGS, "r") as f:
                server_mvp_data = json.loads(f.read().decode('utf-8'))
        except Exception:
            server_mvp_data = {}

        kit_id = f"mvp_{clean_id}"
        server_mvp_data[kit_id] = {
            "MVP_Kit_Name": display_name,
            "Sound_Path_1": f"sounds/mvp/{clean_id}.vsnd_c",
            "SoundEvent": f"CustomMVP.{clean_id}",
            "CanBePreview": True,
            "Message_Chat": True,
            "Message_Center_Bottom": True,
            "Message_Center_Bottom_InSecs": 10
        }
        formatted_json = json.dumps(server_mvp_data, indent=2, ensure_ascii=False)
        with sftp.open(REMOTE_MVP_SETTINGS, "w") as f:
            f.write(formatted_json)
        sftp.close()
        ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
        ssh.close()

        with open(os.path.join(LOCAL_BACKUP, "MVP_Settings.json"), "w", encoding="utf-8") as f:
            f.write(formatted_json)

        yield {"step": 4, "status": "completed", "msg": f"Registered '{display_name}' ({kit_id}) in server database"}
    except Exception as e:
        yield {"step": 4, "status": "failed", "msg": f"Failed to update MVP_Settings.json: {e}"}
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
        shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}_000.vpk"))
        shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}.vpk"))

        ssh = get_ssh_client(timeout=15)
        sftp = ssh.open_sftp()
        for rem_dir in REMOTE_WORKSHOP_PATHS:
            ssh.exec_command(f"mkdir -p {rem_dir}")
            sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
            sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}_000.vpk")
            sftp.put(os.path.join(VPK_DIR, "publish_data.txt"), f"{rem_dir}/publish_data.txt")
        sftp.close()

        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
        ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")
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
            compiled_src = os.path.join(GAME_DIR, "sounds", "mvp", f"{clean_id}.vsnd_c")
            if os.path.exists(compiled_src):
                shutil.copy2(compiled_src, os.path.join(target_sound_dir, f"{clean_id}.vsnd_c"))
        yield {"step": 6, "status": "completed", "msg": "Local game files synchronized"}
    except Exception as e:
        yield {"step": 6, "status": "completed", "msg": f"Local sync notice: {e}"}

    # STEP 7: Finished - Ready to Update in Workshop Pack
    yield {
        "step": 7,
        "status": "completed",
        "msg": f"Anthem '{display_name}' mastered & deployed! Workshop addon wlzMVP is ready to be published to Steam."
    }

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
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}_000.vpk"))
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}.vpk"))

    ssh = get_ssh_client(timeout=15)
    sftp = ssh.open_sftp()
    for rem_dir in REMOTE_WORKSHOP_PATHS:
        ssh.exec_command(f"mkdir -p {rem_dir}")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}_000.vpk")
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
            <div class="card-desc">Add 1 audio file, choose start point, and the system automatically executes the full chronological pipeline: mastering, KV3 compiling, server deployment, and workshop packaging.</div>
          </div>
          <div class="status-badge" style="background:#0a0a0a; border-color:var(--card-border);">
            <span class="status-dot"></span>
            <span>Addon: wlzMVP (3827657422)</span>
          </div>
        </div>

        <div class="summary-grid" style="margin-bottom: 20px;">
          <div class="summary-card">
            <div class="summary-label">Audio Standard</div>
            <div class="summary-val" style="font-size:0.82rem; color:#fff;">10.0s Trim | 1.0s Fadeout | 44.1kHz PCM WAV</div>
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

        <!-- The 1-Step Creator Form -->
        <div style="background: #040404; border: 1px solid var(--card-border); border-radius: 6px; padding: 18px; margin-bottom: 20px;">
          <div style="font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 14px;">
            1. Select Audio Track & Start Point
          </div>

          <div class="form-group">
            <label>Source Audio File</label>
            <div style="display: flex; gap: 8px;">
              <input type="text" id="mvpAudioPath" placeholder="C:\\path\\to\\song.mp3, .wav, or .ogg" oninput="onMvpFileSelected(this.value)">
              <button class="btn btn-secondary" style="white-space: nowrap; padding: 0 16px;" onclick="browseMvpFile()">Browse File</button>
            </div>
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">
              Supports MP3, WAV, OGG, FLAC, M4A. You can browse, paste a path, or drag and drop.
            </div>
          </div>

          <div class="input-row">
            <div class="form-group">
              <label>MVP Display Name</label>
              <input type="text" id="mvpDisplayName" placeholder="e.g. Florin Salam - Saint Tropez">
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">
                How this anthem appears in /mvp menu and round-win announcements.
              </div>
            </div>

            <div class="form-group">
              <label>Start Point (Timestamp)</label>
              <input type="text" id="mvpStartTime" value="00:00:00" placeholder="00:00:00 or 0:45">
              <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">
                Where the 10-second round MVP song starts.
              </div>
            </div>
          </div>

          <div style="margin-top: 6px; margin-bottom: 16px;">
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 6px;">Quick Start Point Presets:</div>
            <div class="color-tags-container">
              <span class="color-tag-pill" onclick="setMvpStartTime('00:00:00')">00:00:00 (Start)</span>
              <span class="color-tag-pill" onclick="setMvpStartTime('00:00:30')">00:00:30</span>
              <span class="color-tag-pill" onclick="setMvpStartTime('00:00:45')">00:00:45</span>
              <span class="color-tag-pill" onclick="setMvpStartTime('00:01:00')">00:01:00</span>
              <span class="color-tag-pill" onclick="setMvpStartTime('00:01:15')">00:01:15</span>
              <span class="color-tag-pill" onclick="setMvpStartTime('00:01:30')">00:01:30</span>
            </div>
          </div>

          <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; margin-top: 10px;">
            <button class="btn" id="btnRunMvpPipeline" onclick="runMvpPipeline()" style="padding: 12px 28px; font-weight: 700; font-size: 0.88rem;">
              Process Audio & Deploy Pipeline
            </button>
          </div>
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

    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.target.classList.add('active');
      if (tabId === 'tab-announcements') loadAnnouncements();
      if (tabId === 'tab-hostname') loadHostname();
      if (tabId === 'tab-convars') loadConvars();
      if (tabId === 'tab-mvp') loadMvpList();
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
      '{Gold}': '#E4AE39',
      '{LightBlue}': '#5E98D9',
      '{Green}': '#40FF40',
      '{LightPurple}': '#D32CE6',
      '{LightYellow}': '#E5E24D',
      '{Red}': '#FF4040',
      '{Default}': '#FFFFFF',
      '{White}': '#FFFFFF',
      '{Grey}': '#CCCCCC',
      '{Lime}': '#40FF40',
      '{Blue}': '#5E98D9',
      '{Purple}': '#D32CE6'
    };

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
        document.getElementById('headerStatusText').innerText = data.online ? `Online (${data.players}/${data.max_players})` : 'Offline';
        document.getElementById('statCs2Status').innerText = data.online ? `Active (${data.map})` : 'Stopped';
        document.getElementById('statCs2Status').style.color = data.online ? '#22c55e' : '#ef4444';
      } catch (e) {}
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
        log(out.message || 'CS2 Tools started.');
        showToast('CS2 Workshop Tools launched.', 'info');
      } catch (e) {
        log('[ERROR] Error starting CS2 tools: ' + e);
        showToast('Error starting tools: ' + e, 'error');
      }
    }

    function openFileConverterPrompt() {
      openConvertModal();
    }

    // All-in-One MVP Pipeline
    const PIPELINE_STEPS = [
      { id: 1, title: 'Trim & Master Audio (10s PCM WAV)', desc: '10.0s trim from start point with 1s fadeout at 44.1kHz 16-bit PCM WAV' },
      { id: 2, title: 'Generate Soundevents KV3 Definition', desc: 'Registers CustomMVP.{id} in soundevents_addon.vsndevts for Source 2 audio' },
      { id: 3, title: 'Compile Assets with resourcecompiler.exe', desc: 'Compiles audio to binary .vsnd_c and soundevents to .vsndevts_c' },
      { id: 4, title: 'Register in Server MVP_Settings.json', desc: 'Activates /mvp WASD menu selection, preview, and round-win announcements' },
      { id: 5, title: 'Pack & Deploy Workshop VPK Cache', desc: 'Builds Valve VPK and synchronizes to server linux workshop directories' },
      { id: 6, title: 'Synchronize Local CS2 Game Files', desc: 'Syncs compiled anthem into your local Steam Counter-Strike 2 directory' },
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

    function setMvpStartTime(val) {
      document.getElementById('mvpStartTime').value = val;
    }

    function onMvpFileSelected(path) {
      if (!path) return;
      const cleanPath = path.trim().replace(/^["']|["']$/g, '');
      const parts = cleanPath.split(/[/\\]/);
      const filename = parts[parts.length - 1];
      const dotIdx = filename.lastIndexOf('.');
      const baseName = dotIdx !== -1 ? filename.substring(0, dotIdx) : filename;
      const formattedName = baseName.replace(/[_-]/g, ' ').split(' ').map(w => w ? w.charAt(0).toUpperCase() + w.slice(1) : '').join(' ');
      const nameInput = document.getElementById('mvpDisplayName');
      if (nameInput && (!nameInput.value || nameInput.dataset.autoFilled === "true")) {
        nameInput.value = formattedName;
        nameInput.dataset.autoFilled = "true";
      }
    }

    async function browseMvpFile() {
      try {
        const res = await fetch('/api/browse_audio_file', { method: 'POST' });
        const data = await res.json();
        if (data.path) {
          document.getElementById('mvpAudioPath').value = data.path;
          onMvpFileSelected(data.path);
        }
      } catch (e) {
        showToast('Error opening file dialog: ' + e, 'error');
      }
    }

    async function runMvpPipeline() {
      const audioPath = document.getElementById('mvpAudioPath').value.trim();
      const displayName = document.getElementById('mvpDisplayName').value.trim();
      const startTime = document.getElementById('mvpStartTime').value.trim() || '00:00:00';

      if (!audioPath) {
        showToast('Please provide an audio file path or click Browse.', 'error');
        return;
      }

      initPipelineStepsUI();
      document.getElementById('mvpPipelineTracker').style.display = 'block';
      document.getElementById('workshopReadyBanner').style.display = 'none';
      document.getElementById('pipelineOverallStatus').innerText = 'Executing Pipeline...';
      document.getElementById('pipelineOverallStatus').style.color = 'var(--gold)';
      const btn = document.getElementById('btnRunMvpPipeline');
      btn.disabled = true;
      btn.innerText = 'Processing Pipeline...';

      log(`[MVP] Starting All-in-One Pipeline for "${displayName || audioPath}"...`);

      try {
        const res = await fetch('/api/mvp/pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ audio_path: audioPath, display_name: displayName, start_time: startTime })
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let hasError = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
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
                showToast('Anthem successfully mastered and deployed!', 'success');
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
        log('[MVP ERROR] Pipeline error: ' + e);
        showToast('Pipeline network error: ' + e, 'error');
      } finally {
        btn.disabled = false;
        btn.innerText = 'Process Audio & Deploy Pipeline';
      }
    }

    async function loadMvpList() {
      const tbody = document.getElementById('mvpAnthemsTableBody');
      if (!tbody) return;
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:18px; color:var(--text-muted);">Loading anthems from server...</td></tr>';

      try {
        const res = await fetch('/api/mvp/list');
        const data = await res.json();
        if (data.anthems && data.anthems.length > 0) {
          tbody.innerHTML = data.anthems.map(a => `
            <tr>
              <td style="padding: 10px 14px; font-weight: 600; color: #fff;">${a.name}</td>
              <td style="padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: #38bdf8;">${a.event}</td>
              <td style="padding: 10px 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: var(--text-muted);">${a.path}</td>
              <td style="padding: 10px 14px; text-align: right;">
                <button class="btn btn-sm btn-danger" onclick="deleteMvp('${a.id}', '${encodeURIComponent(a.name)}')">Delete</button>
              </td>
            </tr>
          `).join('');
        } else {
          tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:18px; color:var(--text-muted);">No custom anthems registered yet.</td></tr>';
        }
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:18px; color:#ef4444;">Error loading anthems: ${e}</td></tr>`;
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
    window.onload = () => {
      refreshServices();
      loadAnnouncements();
      loadMvpList();
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
                        "event": v.get("SoundEvent", ""),
                        "path": v.get("Sound_Path_1", "")
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
        if self.path == "/api/browse_audio_file":
            try:
                p = browse_audio_file()
                self.send_json({"success": True, "path": p})
            except Exception as e:
                self.send_json({"success": False, "error": str(e), "path": ""})
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
            audio_path = req_data.get("audio_path", "").strip(' "\'')
            display_name = req_data.get("display_name", "").strip()
            start_time = req_data.get("start_time", "00:00:00").strip()

            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            try:
                for ev in execute_mvp_pipeline(audio_path, display_name, start_time):
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
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

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
    sys.stdout.reconfigure(encoding='utf-8')
    port = 5890
    server = HTTPServer(("127.0.0.1", port), ControlCenterHandler)
    url = f"http://127.0.0.1:{port}"
    
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print("=" * 65)
    print("        CS2 Server Control Center (Active)")
    print("=" * 65)
    print(f"[*] Server Control Center running at: {url}")
    print("[*] Launching native standalone application window...")

    launched_standalone = False
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
        open_app_window(url)
        print("[*] Standalone GUI unavailable. Opened browser fallback.")
        print("[*] Press Ctrl+C in this terminal window to stop the server.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    server.shutdown()
    print("\n[*] Control Center closed gracefully.")

if __name__ == "__main__":
    main()

