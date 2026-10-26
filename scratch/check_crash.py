import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 120 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
for l in lines:
    if any(k in l.lower() for k in ['crash', 'signal', 'fault', 'segv', 'stopped', 'failed', 'killed', 'error', 'round', 'mvp', 'stopsound', 'playing']):
        print(l)

ssh.close()
