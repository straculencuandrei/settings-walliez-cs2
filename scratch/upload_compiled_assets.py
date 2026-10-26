import os, paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

# Ensure directories exist on server
cmd = "mkdir -p /home/csgoserver/server-cs2/game/csgo/soundevents /home/csgoserver/server-cs2/game/csgo/sounds/mvp /home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/soundevents /home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/sounds/mvp"
stdin, stdout, stderr = ssh.exec_command(cmd)
stdout.channel.recv_exit_status()

sftp = ssh.open_sftp()
win_base = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\wlzMVP"

files_to_sync = [
    (r"soundevents\soundevents_addon.vsndevts_c", "soundevents/soundevents_addon.vsndevts_c"),
    (r"sounds\mvp\stiufeatwalli3zmastered.vsnd_c", "sounds/mvp/stiufeatwalli3zmastered.vsnd_c"),
    (r"sounds\mvp\gta_iii_full_theme_hq.vsnd_c", "sounds/mvp/gta_iii_full_theme_hq.vsnd_c")
]

for rel_win, rel_srv in files_to_sync:
    local_path = os.path.join(win_base, rel_win)
    if os.path.exists(local_path):
        print(f"Uploading {local_path} ({os.path.getsize(local_path)} bytes)...")
        # Upload to game/csgo/
        srv_csgo = f"/home/csgoserver/server-cs2/game/csgo/{rel_srv}"
        sftp.put(local_path, srv_csgo)
        print(f"  -> {srv_csgo}")
        
        # Upload to game/csgo_addons/wlzMVP/
        srv_addon = f"/home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/{rel_srv}"
        sftp.put(local_path, srv_addon)
        print(f"  -> {srv_addon}")

# Also upload addoninfo.txt
addoninfo = os.path.join(win_base, "addoninfo.txt")
if os.path.exists(addoninfo):
    sftp.put(addoninfo, "/home/csgoserver/server-cs2/game/csgo_addons/wlzMVP/addoninfo.txt")

sftp.close()

# Set ownership
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/soundevents /home/csgoserver/server-cs2/game/csgo/sounds/mvp /home/csgoserver/server-cs2/game/csgo_addons/wlzMVP")

print("[+] All compiled vsnd_c and vsndevts_c assets synced to dedicated server!")
ssh.close()
