import paramiko, os, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

local_vpk_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\vpks\3827657422"
remote_workshop_dir = "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422"
old_workshop_dir = "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827649505"

# 1. Create remote dir and remove old
print("[*] Creating remote directory...")
ssh.exec_command(f"rm -rf {old_workshop_dir} && mkdir -p {remote_workshop_dir}")

# 2. Upload files via SFTP
sftp = ssh.open_sftp()
for fname in os.listdir(local_vpk_dir):
    local_path = os.path.join(local_vpk_dir, fname)
    remote_path = f"{remote_workshop_dir}/{fname}"
    print(f"Uploading {fname} ({os.path.getsize(local_path)} bytes)...")
    sftp.put(local_path, remote_path)

# Also create single 3827657422.vpk copy or link if needed by older mount logic
print("[*] Ensuring standard single vpk copy exists...")
ssh.exec_command(f"cp {remote_workshop_dir}/3827657422_000.vpk {remote_workshop_dir}/3827657422.vpk")

# 3. Update multiaddonmanager.cfg
mam_cfg = """// MultiAddonManager Configuration
// Mount custom workshop addons for sounds/models
mm_extra_addons 				"3827657422"
mm_client_extra_addons			""		
mm_extra_addons_timeout			20		
mm_addon_connection_timeout 	30      
mm_addon_mount_download			0		
mm_cache_clients_with_addons	1		
mm_cache_clients_duration		0		
mm_block_disconnect_messages 	1		
mm_addon_debug					1		
"""
with sftp.file("/home/csgoserver/server-cs2/game/csgo/cfg/multiaddonmanager/multiaddonmanager.cfg", "w") as f:
    f.write(mam_cfg)
sftp.close()

# 4. Set ownership and restart
print("[*] Setting file permissions...")
ssh.exec_command(f"chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/")
ssh.exec_command(f"chown csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/cfg/multiaddonmanager/multiaddonmanager.cfg")

print("[*] Restarting cs2 service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command("systemctl status cs2")
print(stdout.read().decode()[:500])

ssh.close()
print("[+] Deployment of 3827657422 complete!")
