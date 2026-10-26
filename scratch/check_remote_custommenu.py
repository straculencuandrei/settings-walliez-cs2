import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command('ls -la /home/csgoserver/cs2-custommenu/')
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('find /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/ -name "*.json"')
print("Plugin configs:\n", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
