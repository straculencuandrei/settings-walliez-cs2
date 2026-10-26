import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")
sftp = ssh.open_sftp()

remote_path = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/CustomMenu/CustomMenu.json"
local_path = r"c:\Users\buzunar\Documents\cs2server\server-configs\plugins\CustomMenu\CustomMenu.json"
os.makedirs(os.path.dirname(local_path), exist_ok=True)
sftp.get(remote_path, local_path)
print("[+] Fetched CustomMenu.json")

sftp.close()
ssh.close()
