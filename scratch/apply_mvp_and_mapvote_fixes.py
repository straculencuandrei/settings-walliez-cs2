import os
import sys
import json
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

print("[*] Connecting to server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=r")(e092e8EjTUiV", timeout=15)
sftp = ssh.open_sftp()

# -------------------------------------------------------------
# 1. Upload updated Custom_MVP_Sounds.cs & compile
# -------------------------------------------------------------
print("[*] Uploading Custom_MVP_Sounds.cs...")
with open("Custom_MVP_Sounds.cs", "r", encoding="utf-8") as f:
    local_cs = f.read()

src_dir = "/home/csgoserver/cs2-custom-mvp"
plugin_dir = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds"

with sftp.file(f"{src_dir}/Custom_MVP_Sounds.cs", "w") as f:
    f.write(local_cs)

print("[*] Building Custom_MVP_Sounds (Release)...")
stdin, stdout, stderr = ssh.exec_command(f"cd {src_dir} && dotnet build -c Release")
out = stdout.read().decode('utf-8', errors='replace')
if "Build succeeded." not in out:
    print("[ERROR] Build failed:\n", out)
    ssh.close()
    sys.exit(1)
print("[+] Custom_MVP_Sounds build succeeded.")

print("[*] Copying compiled binaries...")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.dll {plugin_dir}/Custom_MVP_Sounds.dll")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.deps.json {plugin_dir}/Custom_MVP_Sounds.deps.json")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.pdb {plugin_dir}/Custom_MVP_Sounds.pdb")

# -------------------------------------------------------------
# 2. Update Custom_MVP_Sounds config: MVP_ForceDisableDefaultMVP_ToAll = true
# -------------------------------------------------------------
print("[*] Updating Custom_MVP_Sounds config.json...")
mvp_cfg_path = f"{plugin_dir}/config/config.json"
try:
    with sftp.file(mvp_cfg_path, "r") as f:
        mvp_cfg = json.loads(f.read().decode('utf-8'))
except Exception as e:
    print(f"[-] Could not read {mvp_cfg_path}: {e}")
    mvp_cfg = {}

mvp_cfg["MVP_ForceDisableDefaultMVP_ToAll"] = True
with sftp.file(mvp_cfg_path, "w") as f:
    f.write(json.dumps(mvp_cfg, indent=2))
print("[+] Custom_MVP_Sounds config updated (MVP_ForceDisableDefaultMVP_ToAll: true)")

# -------------------------------------------------------------
# 3. Update WeaponPaints config: MusicEnabled = false
# -------------------------------------------------------------
print("[*] Updating WeaponPaints config (MusicEnabled: false)...")
wp_cfg_path = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/WeaponPaints/WeaponPaints.json"
try:
    with sftp.file(wp_cfg_path, "r") as f:
        wp_cfg = json.loads(f.read().decode('utf-8'))
    if "Additional" in wp_cfg:
        wp_cfg["Additional"]["MusicEnabled"] = False
    with sftp.file(wp_cfg_path, "w") as f:
        f.write(json.dumps(wp_cfg, indent=2))
    print("[+] WeaponPaints config updated (MusicEnabled: false)")
except Exception as e:
    print(f"[-] Error updating WeaponPaints config: {e}")

# -------------------------------------------------------------
# 4. Create gamemodes_server.txt with mg_active mapgroup
# -------------------------------------------------------------
print("[*] Writing gamemodes_server.txt...")
gamemodes_server_txt = """\"GameModes_Server.txt\"
{
    \"gameTypes\"
    {
        \"classic\"
        {
            \"gameModes\"
            {
                \"competitive\"
                {
                    \"mapgroupsMP\"
                    {
                        \"mg_active\"        \"\"
                    }
                }
                \"casual\"
                {
                    \"mapgroupsMP\"
                    {
                        \"mg_active\"        \"\"
                    }
                }
            }
        }
    }
    
    \"mapgroups\"
    {
        \"mg_active\"
        {
            \"name\"              \"mg_active\"
            \"displayname\"       \"Active Duty Maps\"
            \"maps\"
            {
                \"de_mirage\"     \"\"
                \"de_dust2\"      \"\"
                \"de_inferno\"    \"\"
                \"de_nuke\"       \"\"
                \"de_ancient\"    \"\"
                \"de_anubis\"     \"\"
                \"de_train\"      \"\"
                \"de_vertigo\"    \"\"
                \"de_overpass\"   \"\"
                \"cs_office\"     \"\"
            }
        }
    }
}
"""

with sftp.file("/home/csgoserver/server-cs2/game/csgo/gamemodes_server.txt", "w") as f:
    f.write(gamemodes_server_txt)
print("[+] gamemodes_server.txt created successfully.")

# -------------------------------------------------------------
# 5. Create mapcycle.txt and maplist.txt
# -------------------------------------------------------------
print("[*] Writing mapcycle.txt and maplist.txt...")
map_list_content = """de_mirage
de_dust2
de_inferno
de_nuke
de_ancient
de_anubis
de_train
de_vertigo
de_overpass
cs_office
"""
with sftp.file("/home/csgoserver/server-cs2/game/csgo/mapcycle.txt", "w") as f:
    f.write(map_list_content)
with sftp.file("/home/csgoserver/server-cs2/game/csgo/maplist.txt", "w") as f:
    f.write(map_list_content)
print("[+] mapcycle.txt and maplist.txt created.")

# -------------------------------------------------------------
# 6. Create gamemode_competitive_server.cfg & update server.cfg
# -------------------------------------------------------------
print("[*] Configuring end-match voting convars in cfgs...")
endmatch_cfg = """// ==========================================
// Map Voting & End-of-Match Configuration
// ==========================================
mapgroup mg_active
mp_match_end_changelevel 1
mp_match_end_restart 0
mp_endmatch_votenextmap 1
mp_endmatch_votenextmap_keepcurrent 1
mp_endmatch_votenextleveltime 20
"""

with sftp.file("/home/csgoserver/server-cs2/game/csgo/cfg/gamemode_competitive_server.cfg", "w") as f:
    f.write(endmatch_cfg)

# Also append/ensure in server.cfg
with sftp.file("/home/csgoserver/server-cs2/game/csgo/cfg/server.cfg", "r") as f:
    server_cfg_content = f.read().decode('utf-8')

if "mp_match_end_changelevel" not in server_cfg_content:
    server_cfg_content += "\n\n" + endmatch_cfg
    with sftp.file("/home/csgoserver/server-cs2/game/csgo/cfg/server.cfg", "w") as f:
        f.write(server_cfg_content)
print("[+] CFG files updated with end match voting convars.")

# -------------------------------------------------------------
# 7. Update cs2.service to include +mapgroup mg_active
# -------------------------------------------------------------
print("[*] Updating cs2.service with +mapgroup mg_active...")
cs2_service_content = """[Unit]
Description=CS2 Dedicated Server
After=network.target

[Service]
Type=simple
User=csgoserver
Environment=LD_LIBRARY_PATH=/home/csgoserver/server-cs2/game/bin/linuxsteamrt64
WorkingDirectory=/home/csgoserver/server-cs2/game/bin/linuxsteamrt64
ExecStart=/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/cs2 -dedicated +ip 0.0.0.0 -port 27015 +mapgroup mg_active +map de_mirage +game_type 0 +game_mode 1 -maxplayers 24 +sv_setsteamaccount 901325FE0D83A7CBB1F00D4C7FB7C1EE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
with sftp.file("/etc/systemd/system/cs2.service", "w") as f:
    f.write(cs2_service_content)

sftp.close()

# -------------------------------------------------------------
# 8. Set permissions, reload systemd & restart cs2
# -------------------------------------------------------------
print("[*] Reloading systemd and setting ownership...")
ssh.exec_command("systemctl daemon-reload")
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2 /home/csgoserver/cs2-custom-mvp")

print("[*] Restarting cs2 service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

print("[*] Waiting 7 seconds for server startup...")
time.sleep(7)

# Check service status
stdin, stdout, stderr = ssh.exec_command("systemctl is-active cs2")
status = stdout.read().decode('utf-8').strip()
print(f"[+] Service status: {status}")

ssh.close()
print("[+] All files applied and service restarted successfully!")
