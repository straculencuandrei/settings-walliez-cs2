import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 --since '20 minutes ago' --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print(f"Total lines: {len(lines)}")
for l in lines[-80:]:
    print(l)

ssh.close()
