import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command('ls -la /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422')
print("linuxsteamrt64:", stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('ls -la /home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422')
print("server-cs2:", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
