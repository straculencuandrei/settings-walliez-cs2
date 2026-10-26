import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("sed -n '380,410p' /home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs")
print(stdout.read().decode())
ssh.close()
