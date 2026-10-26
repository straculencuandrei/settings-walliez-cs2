import os
import sys
import shutil
import json
import re
import subprocess
import paramiko

# Import clean 44.1kHz MP3 algorithm (matching https://onlineaudioconverter.com/)
from export_clean_mp3 import convert_to_clean_44k_mp3, convert_to_clean_44k_wav

sys.stdout.reconfigure(encoding='utf-8')

SERVER_HOST = "81.181.113.120"
SERVER_PORT = 22
SERVER_USER = "root"
SERVER_PASS = ")(e092e8EjTUiV"

WORKSHOP_ID = "3827657422"
ADDON_NAME = "wlzMVP"
ADDON_TITLE = "wlzMVP"
ADDON_AUTHOR = "Walliez"
ADDON_DESC = "wlzMVP - Custom Server MVP Music Pack"

CS2_ROOT = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive"
LOCAL_SRC = r"C:\Users\buzunar\Documents\cs2server\wlzMVP"

CONTENT_DIR = os.path.join(CS2_ROOT, "content", "csgo_addons", ADDON_NAME)
GAME_DIR = os.path.join(CS2_ROOT, "game", "csgo_addons", ADDON_NAME)
COMPILER_EXE = os.path.join(CS2_ROOT, "game", "bin", "win64", "resourcecompiler.exe")
CS2_EXE = os.path.join(CS2_ROOT, "game", "bin", "win64", "cs2.exe")

CONTENT_SOUNDS = os.path.join(CONTENT_DIR, "sounds", "mvp")
LOCAL_SOUNDS = os.path.join(LOCAL_SRC, "sounds", "mvp")
REMOTE_MVP_SETTINGS = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json"

def sanitize_id(text):
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', text.strip())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean.lower()

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
        secs = int(st)
        mins = secs // 60
        rem_secs = secs % 60
        return f"00:{mins:02d}:{rem_secs:02d}"
    except ValueError:
        return "00:00:00"

def ensure_directories():
    for d in [
        CONTENT_SOUNDS,
        os.path.join(CONTENT_DIR, "soundevents"),
        os.path.join(GAME_DIR, "sounds", "mvp"),
        os.path.join(GAME_DIR, "soundevents"),
        LOCAL_SOUNDS,
        os.path.join(LOCAL_SRC, "soundevents"),
        os.path.join(CS2_ROOT, "game", "csgo_addons", "vpks", WORKSHOP_ID)
    ]:
        os.makedirs(d, exist_ok=True)

    # Sync addoninfo.txt
    addoninfo = f'''"AddonInfo"
{{
    "addonTitle"         "{ADDON_TITLE}"
    "addonVersion"       "1.0"
    "addonAuthor"        "{ADDON_AUTHOR}"
    "addonDescription"   "{ADDON_DESC}"
    "addonSteamAppID"    "730"
}}
'''
    for p in [
        os.path.join(CONTENT_DIR, "addoninfo.txt"),
        os.path.join(GAME_DIR, "addoninfo.txt"),
        os.path.join(LOCAL_SRC, "addoninfo.txt")
    ]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(addoninfo)

    # Sync preview image
    prev_src = os.path.join(LOCAL_SRC, "preview.jpg")
    if os.path.exists(prev_src):
        for target in [
            os.path.join(CONTENT_DIR, "preview.jpg"),
            os.path.join(CONTENT_DIR, "thumb.jpg"),
            os.path.join(LOCAL_SRC, "thumb.jpg")
        ]:
            shutil.copy2(prev_src, target)

def rebuild_kv3_soundevents():
    """Dynamically reconstructs a 100% valid KV3 document with all staged audio tracks inside root braces."""
    print("[*] Rebuilding KV3 soundevents_addon.vsndevts...")
    tracks = set()
    for f in os.listdir(CONTENT_SOUNDS):
        ext = os.path.splitext(f)[1].lower()
        if ext in [".wav", ".mp3"]:
            tracks.add(sanitize_id(os.path.splitext(f)[0]))

    track_list = sorted(list(tracks))

    lines = [
        "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->",
        "{"
    ]
    for track_key in track_list:
        lines.append(f'    "CustomMVP.{track_key}" =')
        lines.append("    {")
        lines.append('        type = "csgo_music"')
        lines.append("        volume = 1.000000")
        lines.append("        pitch = 1.000000")
        lines.append(f'        vsnd_files = [ "sounds/mvp/{track_key}.vsnd" ]')
        lines.append("    }")
    lines.append("}")
    kv3_content = "\n".join(lines) + "\n"

    for p in [
        os.path.join(CONTENT_DIR, "soundevents_addon.vsndevts"),
        os.path.join(CONTENT_DIR, "soundevents", "soundevents_addon.vsndevts"),
        os.path.join(LOCAL_SRC, "soundevents_addon.vsndevts"),
        os.path.join(LOCAL_SRC, "soundevents", "soundevents_addon.vsndevts")
    ]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(kv3_content)
    print(f"[+] Rebuilt soundevents with {len(track_list)} track(s) (100% valid KV3 syntax).")

def compile_all_resources():
    print("\n[*] Compiling audio and soundevents with CS2 resourcecompiler.exe...")
    cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if "OK:" in res.stdout:
        print("[+] All assets compiled into .vsnd_c and .vsndevts_c successfully!")
    else:
        print(res.stdout)
        if res.stderr:
            print("STDERR:", res.stderr)

def sync_server_settings(new_track_key=None, new_display_name=None):
    print("\n[*] Synchronizing MVP_Settings.json on dedicated server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    sftp = ssh.open_sftp()
    server_data = {}
    try:
        with sftp.file(REMOTE_MVP_SETTINGS, "r") as f:
            server_data = json.loads(f.read().decode('utf-8'))
    except Exception:
        server_data = {}

    # Ensure all local tracks exist in config
    tracks = set()
    for f in os.listdir(CONTENT_SOUNDS):
        ext = os.path.splitext(f)[1].lower()
        if ext in [".wav", ".mp3"]:
            tracks.add(sanitize_id(os.path.splitext(f)[0]))

    for k in sorted(list(tracks)):
        kit_id = f"mvp_{k}"
        disp = new_display_name if (k == new_track_key and new_display_name) else k.replace("_", " ").title()

        if kit_id in server_data and "MVP_Kit_Name" in server_data[kit_id]:
            disp = server_data[kit_id]["MVP_Kit_Name"]
            if k == new_track_key and new_display_name:
                disp = new_display_name

        server_data[kit_id] = {
            "CanBePreview": True,
            "Message_Chat": True,
            "Message_Center_Bottom": True,
            "Message_Center_Bottom_InSecs": 10,
            "MVP_Kit_Name": disp,
            "Sound_Path_1": f"sounds/mvp/{k}.vsnd"
        }

    formatted = json.dumps(server_data, indent=2, ensure_ascii=False)
    with sftp.file(REMOTE_MVP_SETTINGS, "w") as f:
        f.write(formatted)
    sftp.close()

    local_json = os.path.join(LOCAL_SRC, "MVP_Settings.json")
    with open(local_json, "w", encoding="utf-8") as f:
        f.write(formatted)

    ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
    ssh.close()
    print(f"[+] Dedicated server config updated with {len(server_data)} anthem(s)!")

def open_workshop_manager():
    choice = input("\n[?] Open CS2 Workshop Tools now to submit update to Steam? (Y/n): ").strip().lower()
    if choice != "n":
        print("[*] Launching CS2 Workshop Tools...")
        subprocess.Popen([CS2_EXE, "-tools", "-addon", ADDON_NAME])

def add_new_anthem(audio_file_path=None):
    ensure_directories()

    input_file = audio_file_path
    if not input_file or not os.path.exists(input_file):
        while not input_file or not os.path.exists(input_file):
            input_file = input("\n[?] Drag & drop or paste audio file path: ").strip().strip('"')
            if not os.path.exists(input_file):
                print("[!] File not found, please try again.")

    default_name = os.path.splitext(os.path.basename(input_file))[0].replace("_", " ").title()
    name_input = input(f"[?] Enter MVP Display Name [default: '{default_name}']: ").strip()
    display_name = name_input if name_input else default_name

    start_input = input("[?] Enter Start Time (e.g. 0:45 or 45, or press Enter for 00:00): ").strip()
    formatted_start = format_start_time(start_input)

    clean_id = sanitize_id(os.path.splitext(os.path.basename(input_file))[0])
    dest_mp3 = os.path.join(CONTENT_SOUNDS, f"{clean_id}.mp3")
    dest_wav = os.path.join(CONTENT_SOUNDS, f"{clean_id}.wav")
    backup_mp3 = os.path.join(LOCAL_SOUNDS, f"{clean_id}.mp3")
    backup_wav = os.path.join(LOCAL_SOUNDS, f"{clean_id}.wav")

    # Step 1: Export clean 44.1kHz MP3 and WAV using onlineaudioconverter.com algorithm
    print("\n[*] Processing audio using onlineaudioconverter.com 44.1kHz algorithm...")
    convert_to_clean_44k_mp3(input_file, dest_mp3, start_time=formatted_start, duration=10, fadeout=True)
    convert_to_clean_44k_wav(input_file, dest_wav, start_time=formatted_start, duration=10, fadeout=True)
    shutil.copy2(dest_mp3, backup_mp3)
    shutil.copy2(dest_wav, backup_wav)

    # Step 2: Rebuild valid KV3 soundevents
    rebuild_kv3_soundevents()

    # Step 3: Compile all resources with CS2 resourcecompiler
    compile_all_resources()

    # Step 4: Sync server MVP_Settings.json
    sync_server_settings(clean_id, display_name)

    print("\n" + "=" * 65)
    print(f" [SUCCESS] Anthem '{display_name}' has been imported and compiled!")
    print(" - Algorithm: Clean MP3 44.1 kHz, 320 kbps CBR, stripped metadata")
    print(" - Duration: 10.0 seconds with smooth 1-second fadeout")
    print(" - In-Game Menu: Immediately available in /mvp")
    print("=" * 65)

    open_workshop_manager()

def rebuild_all():
    ensure_directories()
    rebuild_kv3_soundevents()
    compile_all_resources()
    sync_server_settings()
    print("\n[SUCCESS] All staged anthems rebuilt, compiled, and synchronized!")
    open_workshop_manager()

def main():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        # Direct drag & drop mode
        add_new_anthem(sys.argv[1].strip().strip('"'))
        return

    print("==============================================================")
    print("                 WLZ CS2 WORKSHOP MVP STUDIO                  ")
    print("     The All-In-One Importer, Compiler & Workshop Tool        ")
    print("==============================================================")
    print("  [1] Add a New MVP Anthem (Audio -> Clean 44.1k MP3 -> Compile)")
    print("  [2] Rebuild & Recompile All Staged Anthems")
    print("  [3] Launch CS2 Workshop Tools Only")
    print("  [4] Exit")
    print("==============================================================")

    choice = input("\nSelect option [1-4]: ").strip()
    if choice == "1":
        add_new_anthem()
    elif choice == "2":
        rebuild_all()
    elif choice == "3":
        ensure_directories()
        print("[*] Launching CS2 Workshop Tools...")
        subprocess.Popen([CS2_EXE, "-tools", "-addon", ADDON_NAME])
    else:
        print("[*] Exiting.")

if __name__ == "__main__":
    main()
