import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl -u cs2 --since "15:35:00" --until "15:39:35" --no-pager | tail -n 60
"""
stdin, stdout, stderr = ssh.exec_command(script)
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
for l in lines:
    print(l)

ssh.close()
