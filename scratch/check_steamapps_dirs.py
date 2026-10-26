import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("ls -la /home/csgoserver/server-cs2/steamapps/")
print("server-cs2/steamapps:\n", stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("ls -la /home/csgoserver/Steam/steamapps/")
print("Steam/steamapps:\n", stdout.read().decode())

ssh.close()
