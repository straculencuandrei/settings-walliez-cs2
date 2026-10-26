import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("sed -n '15,60p' /home/csgoserver/cs2-custom-mvp/Config/Helper.cs")
print("=== Helper.cs ===")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command("md5sum /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.dll /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll")
print("=== MD5SUM ===")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 50 --no-pager")
print("=== CS2 JOURNAL ===")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
