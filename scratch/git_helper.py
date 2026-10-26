import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("cd /home/csgoserver/cs2-custom-mvp && git checkout Config/Helper.cs && git status")
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
