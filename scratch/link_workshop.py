import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

# Create workshop directories and symlinks
cmds = [
    "mkdir -p /home/csgoserver/Steam/steamapps/workshop/content/730/3827657422",
    "mkdir -p /home/csgoserver/Steam/steamapps/workshop/downloads/730",
    "mkdir -p /home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422",
    "mkdir -p /home/csgoserver/server-cs2/steamapps/workshop/downloads/730",
    "cp -ru /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422/* /home/csgoserver/Steam/steamapps/workshop/content/730/3827657422/",
    "cp -ru /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422/* /home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422/",
    "chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop",
    "chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop",
    "chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop",
]

for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()

print("[*] Restarting cs2...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

ssh.close()
print("[+] Synced workshop across all Steam paths and restarted!")
