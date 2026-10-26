import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("objdump -dC /home/csgoserver/server-cs2/game/csgo/addons/multiaddonmanager/bin/multiaddonmanager.so | grep -B 10 -A 20 'steamapps/workshop' || true")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("find /home/csgoserver/ -name '*3827657422*' 2>/dev/null")
print("Found 3827657422 files:\n", stdout.read().decode())

ssh.close()
