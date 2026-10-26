import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command('find /home/csgoserver/server-cs2/game/csgo/addons/ -name "*multiaddon*" -o -name "*mam*"')
print("MAM files:\n", stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('find /home/csgoserver/server-cs2/game/csgo/cfg/ -name "*.cfg" -o -name "*.json"')
print("CFG files:\n", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
