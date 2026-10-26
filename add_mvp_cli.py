import os
import sys
import shutil
import json
import re
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
    return clean.lower()

def format_start_time(st):
    st = st.strip()
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

def convert_audio(input_file, output_wav, start_time="00:00:00"):
    print(f"\n[*] Connecting to conversion server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    fname = sanitize_id(os.path.splitext(os.path.basename(input_file))[0])
    remote_in = f"/tmp/mvp_in_{fname}.tmp"
    remote_wav = f"/tmp/mvp_out_{fname}.wav"

    print(f"[*] Uploading source audio for processing...")
    sftp = ssh.open_sftp()
    sftp.put(input_file, remote_in)

    # Cut to exactly 10 seconds with 1-second fadeout from 9.0s to 10.0s
    print(f"[*] Trimming to 10s with smooth fadeout at 9s (Start: {start_time})...")
    cmd = f"/usr/local/bin/ffmpeg -y -ss {start_time} -i {remote_in} -t 10 -af 'afade=t=out:st=9:d=1' -c:a pcm_s16le -ar 44100 {remote_wav}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()

    sftp.get(remote_wav, output_wav)
    sftp.close()

    ssh.exec_command(f"rm -f {remote_in} {remote_wav}")
    ssh.close()
    print(f"[+] Mastered 10-second broadcast WAV created: {output_wav} ({os.path.getsize(output_wav):,} bytes)")

def update_soundevents(clean_id):
    content_vsndevts = os.path.join(CONTENT_DIR, "soundevents_addon.vsndevts")
    content_sub_vsndevts = os.path.join(CONTENT_DIR, "soundevents", "soundevents_addon.vsndevts")
    local_vsndevts = os.path.join(LOCAL_BACKUP, "soundevents_addon.vsndevts")

    entry = f'''
"CustomMVP.{clean_id}" = 
{{
    type = "csgo_music"
    volume = 1.000000
    vsnd_files = 
    [
        "sounds/mvp/{clean_id}.vsnd",
    ]
}}
'''
    for fpath in [content_vsndevts, content_sub_vsndevts, local_vsndevts]:
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        current = ""
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                current = f.read()
        if f"CustomMVP.{clean_id}" not in current:
            with open(fpath, "a", encoding="utf-8") as f:
                f.write(entry)
            print(f"[+] Updated {os.path.basename(fpath)}")

def compile_assets():
    print("[*] Compiling resources with resourcecompiler.exe...")
    cmd = [COMPILER_EXE, "-r", "-f", "-i", f"{CONTENT_DIR}\\*.*"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if "OK:" in res.stdout:
        print("[+] Resource compilation successful!")
    else:
        print(res.stdout)

def update_server_json(clean_id, display_name):
    print("[*] Updating MVP_Settings.json on server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    sftp = ssh.open_sftp()
    data = {}
    try:
        with sftp.file(REMOTE_MVP_SETTINGS, "r") as f:
            data = json.loads(f.read().decode('utf-8'))
    except Exception:
        data = {}

    kit_key = f"mvp_{clean_id}"
    data[kit_key] = {
        "MVP_Kit_Name": display_name,
        "Sound_Path_1": f"sounds/mvp/{clean_id}.vsnd_c",
        "SoundEvent": f"CustomMVP.{clean_id}",
        "CanBePreview": True,
        "Message_Chat": True,
        "Message_Center_Bottom": True,
        "Message_Center_Bottom_InSecs": 10
    }

    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
    with sftp.file(REMOTE_MVP_SETTINGS, "w") as f:
        f.write(formatted_json)
    sftp.close()

    # Also save local copy
    local_json = os.path.join(LOCAL_BACKUP, "MVP_Settings.json")
    with open(local_json, "w", encoding="utf-8") as f:
        f.write(formatted_json)

    ssh.exec_command(f"chown csgoserver:csgoserver {REMOTE_MVP_SETTINGS}")
    ssh.close()
    print(f"[+] '{display_name}' registered in MVP_Settings.json!")

def package_and_upload_vpk():
    print("[*] Packaging updated VPK with python-vpk...")
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

    addoninfo = os.path.join(GAME_DIR, "addoninfo.txt")
    if os.path.exists(addoninfo):
        shutil.copyfile(addoninfo, os.path.join(staging, "addoninfo.txt"))

    temp_vpk = os.path.join(tempfile.gettempdir(), f"{WORKSHOP_ID}.vpk")
    pak = vpk.new(staging)
    pak.save(temp_vpk)
    shutil.rmtree(staging)
    print(f"[+] Packed VPK: {os.path.getsize(temp_vpk):,} bytes")

    # Update local vpks folder
    os.makedirs(VPK_DIR, exist_ok=True)
    shutil.copyfile(temp_vpk, os.path.join(VPK_DIR, f"{WORKSHOP_ID}_000.vpk"))

    # Upload to server
    print("[*] Deploying VPK to dedicated server workshop cache...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS, timeout=15)

    sftp = ssh.open_sftp()
    for rem_dir in REMOTE_WORKSHOP_PATHS:
        ssh.exec_command(f"mkdir -p {rem_dir}")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}.vpk")
        sftp.put(temp_vpk, f"{rem_dir}/{WORKSHOP_ID}_000.vpk")
    sftp.close()

    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
    ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")
    ssh.close()
    os.remove(temp_vpk)
    print("[+] VPK successfully synchronized across all server workshop paths!")

def main():
    print("======================================================")
    print("        WLZ MVP STUDIO - HIGH-SPEED CLI ADDON         ")
    print("   10s Auto-Trim | 1s Smooth Fadeout | Instant Sync   ")
    print("======================================================")

    # 1. Get input audio file
    input_file = ""
    if len(sys.argv) > 1 and sys.argv[1].strip():
        input_file = sys.argv[1].strip().strip('"')
    
    while not input_file or not os.path.exists(input_file):
        input_file = input("\n[?] Drag & drop or paste the audio file path: ").strip().strip('"')
        if not os.path.exists(input_file):
            print("[!] File not found, please try again.")

    default_name = os.path.splitext(os.path.basename(input_file))[0].replace("_", " ").title()
    name_input = input(f"[?] Enter MVP Display Name [default: '{default_name}']: ").strip()
    display_name = name_input if name_input else default_name

    start_input = input("[?] Enter Start Time (e.g. 0:45 or 45, or press Enter for 00:00): ").strip()
    formatted_start = format_start_time(start_input)

    clean_id = sanitize_id(os.path.splitext(os.path.basename(input_file))[0])

    # Ensure local directory structure
    for d in [
        os.path.join(CONTENT_DIR, "sounds", "mvp"),
        os.path.join(CONTENT_DIR, "soundevents"),
        os.path.join(LOCAL_BACKUP, "sounds", "mvp"),
        os.path.join(LOCAL_BACKUP, "soundevents")
    ]:
        os.makedirs(d, exist_ok=True)

    dest_wav = os.path.join(CONTENT_DIR, "sounds", "mvp", f"{clean_id}.wav")
    backup_wav = os.path.join(LOCAL_BACKUP, "sounds", "mvp", f"{clean_id}.wav")

    # Step 1: Convert/trim to 10s with 1s fadeout
    convert_audio(input_file, dest_wav, formatted_start)
    shutil.copyfile(dest_wav, backup_wav)

    # Step 2: Update soundevents_addon.vsndevts
    update_soundevents(clean_id)

    # Step 3: Compile with resourcecompiler
    compile_assets()

    # Step 4: Update MVP_Settings.json on server
    update_server_json(clean_id, display_name)

    # Step 5: Package VPK and upload to server
    package_and_upload_vpk()

    print("\n======================================================")
    print(f" [SUCCESS] Anthem '{display_name}' is fully deployed!")
    print(" - Audio: 10.0 seconds with smooth 1s fadeout (at 9s)")
    print(" - Menu: Available in /mvp with WASD menu")
    print(" - Server: VPK cache & config updated immediately")
    print("======================================================")

    choice = input("\n[?] Open CS2 Workshop Tools now to push update to Steam? (Y/n): ").strip().lower()
    if choice != "n":
        print("[*] Launching CS2 Workshop Tools...")
        subprocess.Popen([CS2_EXE, "-tools", "-addon", ADDON_NAME])

if __name__ == "__main__":
    main()
