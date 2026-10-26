import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

local_vpk = r"C:\Users\buzunar\Documents\cs2server\scratch\test_pack.vpk"
local_vpk_size = os.path.getsize(local_vpk)
print(f"Uploading trimmed VPK ({local_vpk_size:,} bytes)...")

sftp = ssh.open_sftp()
dest_dirs = [
    "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422",
    "/home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422",
    "/home/csgoserver/Steam/steamapps/workshop/content/730/3827657422"
]

for d in dest_dirs:
    ssh.exec_command(f"mkdir -p {d}")
    remote_single = f"{d}/3827657422.vpk"
    remote_000 = f"{d}/3827657422_000.vpk"
    print(f"Uploading to {remote_single}...")
    sftp.put(local_vpk, remote_single)
    sftp.put(local_vpk, remote_000)

sftp.close()

# Update ownership
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")

print("[+] Trimmed VPK deployed to all server workshop locations!")
ssh.close()
