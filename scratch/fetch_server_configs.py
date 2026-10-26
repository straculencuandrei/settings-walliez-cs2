import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")
sftp = ssh.open_sftp()

files_to_fetch = [
    ("/home/csgoserver/server-cs2/game/csgo/cfg/multiaddonmanager/multiaddonmanager.cfg", "server-configs/cfg/multiaddonmanager.cfg"),
    ("/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json", "server-configs/plugins/Custom_MVP_Sounds/MVP_Settings.json"),
    ("/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs", "server-configs/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.cs"),
    ("/home/csgoserver/cs2-custommenu/CustomMenu.cs", "server-configs/plugins/CustomMenu/CustomMenu.cs"),
    ("/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu/CustomMenu.json", "server-configs/plugins/CustomMenu/CustomMenu.json"),
]

for remote_path, local_rel in files_to_fetch:
    local_path = os.path.join(r"c:\Users\buzunar\Documents\cs2server", local_rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        sftp.get(remote_path, local_path)
        print(f"[+] Fetched {remote_path} -> {local_rel}")
    except Exception as e:
        print(f"[-] Failed {remote_path}: {e}")

sftp.close()
ssh.close()
