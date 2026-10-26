import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("find /var/lib/systemd/coredump/ /tmp/ /home/csgoserver/ -name '*core*' 2>/dev/null")
print("Cores:\n", stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command("coredumpctl info 17819 2>/dev/null")
print("Coredumpctl:\n", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
