import paramiko, sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 --since '13:35:00' --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print(f"Total lines: {len(lines)}")
for l in lines:
    if any(k in l.lower() for k in ['crash', 'segv', 'error', 'failed', 'preview', 'gta', 'mvp', 'play', 'dumped', 'stopped', 'killed', 'command']):
        print(l)

ssh.close()
