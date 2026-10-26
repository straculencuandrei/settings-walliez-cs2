import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("find /home/csgoserver/ -type d -name 'steamapps' 2>/dev/null")
print("steamapps directories:\n", stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("find /home/csgoserver/ -type d -name 'workshop' 2>/dev/null")
print("workshop directories:\n", stdout.read().decode())

ssh.close()
