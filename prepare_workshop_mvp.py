import os
import sys
import shutil
import json
import re
import time
import subprocess
import tempfile
import paramiko
import vpk

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

def convert_to_pcm_wav(input_file, output_wav, start_time="00:00:00"):
    """Uses server ffmpeg to trim audio to exactly 10 seconds with 1-second smooth fadeout."""
    base_name = os.path.basename(input_file)
    print(f"[*] Processing audio '{base_name}' (10s trim, 1s fadeout from 9s)...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    clean_tag = sanitize_id(os.path.splitext(base_name)[0])
    remote_in = f"/tmp/prep_in_{clean_tag}.tmp"
    remote_wav = f"/tmp/prep_out_{clean_tag}.wav"

    sftp = ssh.open_sftp()
    sftp.put(input_file, remote_in)

    cmd = f"/usr/local/bin/ffmpeg -y -ss {start_time} -i {remote_in} -t 10 -af 'afade=t=out:st=9:d=1' -c:a pcm_s16le -ar 44100 {remote_wav}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()

    sftp.get(remote_wav, output_wav)
    sftp.close()

    ssh.exec_command(f"rm -f {remote_in} {remote_wav}")
    ssh.close()
    print(f"[+] Mastered WAV created: {output_wav} ({os.path.getsize(output_wav):,} bytes)")

def rebuild_and_package(audio_inputs=None):
    print("=" * 65)
    print("      CS2 WORKSHOP ADDON PACKAGER & COMPILER (wlzMVP)")
    print("   10s Mastered Trim | Auto-Compile | VPK Build | Fast Sync")
    print("=" * 65)

    # 1. Ensure required directory trees
    for d in [
        os.path.join(CONTENT_DIR, "sounds", "mvp"),
        os.path.join(CONTENT_DIR, "soundevents"),
        os.path.join(GAME_DIR, "sounds", "mvp"),
        os.path.join(GAME_DIR, "soundevents"),
        os.path.join(LOCAL_SRC, "sounds", "mvp"),
        os.path.join(LOCAL_SRC, "soundevents"),
        VPK_DIR
    ]:
        os.makedirs(d, exist_ok=True)

    # 2. Collect audio inputs
    if not audio_inputs:
        audio_inputs = []
        # Check files already placed in local wlzMVP/sounds/mvp/
        local_mvp_dir = os.path.join(LOCAL_SRC, "sounds", "mvp")
        if os.path.exists(local_mvp_dir):
            for f in os.listdir(local_mvp_dir):
                if f.lower().endswith((".mp3", ".wav", ".ogg", ".flac")):
                    full = os.path.join(local_mvp_dir, f)
                    if full not in audio_inputs:
                        audio_inputs.append(full)

    if not audio_inputs:
        print("[!] No audio files provided or found in wlzMVP/sounds/mvp/.")
        return

    # Clean out any old raw MP3s from content folder to prevent compiling 3+ minute tracks
    content_sounds_dir = os.path.join(CONTENT_DIR, "sounds", "mvp")
    for f in os.listdir(content_sounds_dir):
        if f.lower().endswith(".mp3"):
            try:
                os.remove(os.path.join(content_sounds_dir, f))
            except Exception:
                pass

    staged_tracks = []
    # Track metadata mapping
    processed_keys = set()

    for src_path in audio_inputs:
        if not os.path.exists(src_path):
            print(f"[!] Warning: File not found: {src_path}")
            continue

        raw_base = os.path.splitext(os.path.basename(src_path))[0]
        track_key = sanitize_id(raw_base)
        if track_key in processed_keys:
            continue
        processed_keys.add(track_key)

        display_name = raw_base.replace("_", " ").title()

        target_wav_content = os.path.join(CONTENT_DIR, "sounds", "mvp", f"{track_key}.wav")
        target_wav_local = os.path.join(LOCAL_SRC, "sounds", "mvp", f"{track_key}.wav")

        # Convert to 10s broadcast WAV with 1s fadeout
        convert_to_pcm_wav(src_path, target_wav_content)
        shutil.copy2(target_wav_content, target_wav_local)

        staged_tracks.append((display_name, track_key))

    # 3. Synchronize preview images
    preview_src = os.path.join(LOCAL_SRC, "preview.jpg")
    if os.path.exists(preview_src):
        for target in [
            os.path.join(CONTENT_DIR, "preview.jpg"),
            os.path.join(CONTENT_DIR, "thumb.jpg"),
            os.path.join(LOCAL_SRC, "thumb.jpg")
        ]:
            shutil.copy2(preview_src, target)

    # 4. Generate soundevents_addon.vsndevts
    soundevents_lines = [
        "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->",
        "{"
    ]
    for display_title, track_key in staged_tracks:
        soundevents_lines.append(f'    "CustomMVP.{track_key}" =')
        soundevents_lines.append("    {")
        soundevents_lines.append('        type = "csgo_music"')
        soundevents_lines.append("        volume = 1.000000")
        soundevents_lines.append("        pitch = 1.000000")
        soundevents_lines.append(f'        vsnd_files = [ "sounds/mvp/{track_key}.vsnd" ]')
        soundevents_lines.append("    }")
    soundevents_lines.append("}")
    vsndevts_content = "\n".join(soundevents_lines) + "\n"

    for target in [
        os.path.join(CONTENT_DIR, "soundevents", "soundevents_addon.vsndevts"),
        os.path.join(CONTENT_DIR, "soundevents_addon.vsndevts"),
        os.path.join(LOCAL_SRC, "soundevents", "soundevents_addon.vsndevts"),
        os.path.join(LOCAL_SRC, "soundevents_addon.vsndevts"),
    ]:
        with open(target, "w", encoding="utf-8") as f:
            f.write(vsndevts_content)

    # 5. Generate addoninfo.txt
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
        os.path.join(LOCAL_SRC, "addoninfo.txt"),
    ]:
        with open(target, "w", encoding="utf-8") as f:
            f.write(addoninfo_text)

    # 6. Compile resources using resourcecompiler.exe
    print("\n[*] Compiling audio and soundevents using resourcecompiler.exe...")
    cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if "OK:" in res.stdout:
        print("[+] Resource compilation completed successfully!")
    else:
        print(res.stdout)

    # 7. Package into standard Valve VPK
    print("\n[*] Packaging compiled assets into Valve VPK...")
    staging = tempfile.mkdtemp()
    os.makedirs(os.path.join(staging, "sounds", "mvp"), exist_ok=True)
    os.makedirs(os.path.join(staging, "soundevents"), exist_ok=True)

    game_mvp_dir = os.path.join(GAME_DIR, "sounds", "mvp")
    for f in os.listdir(game_mvp_dir):
        if f.endswith(".vsnd_c"):
            shutil.copyfile(os.path.join(game_mvp_dir, f), os.path.join(staging, "sounds", "mvp", f))

    se_c = os.path.join(GAME_DIR, "soundevents_addon.vsndevts_c")
    if os.path.exists(se_c):
        shutil.copyfile(se_c, os.path.join(staging, "soundevents_addon.vsndevts_c"))
        shutil.copyfile(se_c, os.path.join(staging, "soundevents", "soundevents_addon.vsndevts_c"))

    shutil.copyfile(os.path.join(GAME_DIR, "addoninfo.txt"), os.path.join(staging, "addoninfo.txt"))

    temp_vpk = os.path.join(tempfile.gettempdir(), f"{WORKSHOP_ID}.vpk")
    pak = vpk.new(staging)
    pak.save(temp_vpk)
    shutil.rmtree(staging)
    vpk_size = os.path.getsize(temp_vpk)
    print(f"[+] VPK Packaged successfully: {vpk_size:,} bytes (~{vpk_size / 1024 / 1024:.2f} MB)")

    # Write publish_data.txt
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

    # Save to local vpks directory
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}_000.vpk"))
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}.vpk"))

    # 8. Update MVP_Settings.json and sync to server
    print("\n[*] Updating MVP_Settings.json on dedicated server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    sftp = ssh.open_sftp()
    server_mvp_data = {}
    try:
        with sftp.file(REMOTE_MVP_SETTINGS, "r") as f:
            server_mvp_data = json.loads(f.read().decode('utf-8'))
    except Exception:
        server_mvp_data = {}

    for display_title, track_key in staged_tracks:
        kit_id = f"mvp_{track_key}"
        server_mvp_data[kit_id] = {
            "MVP_Kit_Name": display_title,
            "Sound_Path_1": f"sounds/mvp/{track_key}.vsnd_c",
            "SoundEvent": f"CustomMVP.{track_key}",
            "CanBePreview": True,
            "Message_Chat": True,
            "Message_Center_Bottom": True,
            "Message_Center_Bottom_InSecs": 10
        }

    formatted_json = json.dumps(server_mvp_data, indent=2, ensure_ascii=False)
    with sftp.file(REMOTE_MVP_SETTINGS, "w") as f:
        f.write(formatted_json)

    with open(os.path.join(LOCAL_SRC, "MVP_Settings.json"), "w", encoding="utf-8") as f:
        f.write(formatted_json)

    # 9. Deploy VPK to all server workshop locations
    print("[*] Deploying VPK directly to dedicated server workshop cache...")
    for rem_dir in REMOTE_WORKSHOP_PATHS:
        ssh.exec_command(f"mkdir -p {rem_dir}")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}_000.vpk")
        sftp.put(os.path.join(VPK_DIR, "publish_data.txt"), f"{rem_dir}/publish_data.txt")

    sftp.close()

    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")
    ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
    ssh.close()
    os.remove(temp_vpk)

    print("\n" + "=" * 65)
    print("      CS2 WORKSHOP ADDON PACKAGED & DEPLOYED!")
    print("=" * 65)
    print(f"Addon Name:    {ADDON_NAME} (ID: {WORKSHOP_ID})")
    print(f"VPK File Size: {vpk_size:,} bytes (~{vpk_size / 1024 / 1024:.2f} MB)")
    print("\nPackaged Anthems:")
    for display_title, track_key in staged_tracks:
        print(f" - {display_title} (sounds/mvp/{track_key}.vsnd_c) [10s Mastered]")
    print("=" * 65)

    choice = input("\n[?] Open CS2 Workshop Tools now to submit update to Steam? (Y/n): ").strip().lower()
    if choice != "n":
        print("[*] Launching CS2 Workshop Tools...")
        subprocess.Popen([CS2_EXE, "-tools", "-addon", ADDON_NAME])

if __name__ == "__main__":
    inputs = sys.argv[1:]
    rebuild_and_package(inputs if inputs else None)
