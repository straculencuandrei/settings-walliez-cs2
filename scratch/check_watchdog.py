import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -S '2026-10-26 14:54:00' -U '2026-10-26 14:56:05' --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print(f"Total lines: {len(lines)}")
for l in lines:
    print(l)

ssh.close()
