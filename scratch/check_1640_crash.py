import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

cmd = r'''journalctl -u cs2 --since "2026-10-26 16:40:00" --until "2026-10-26 16:41:45" --no-pager'''
lines = run(cmd).splitlines()
print(f"Total lines: {len(lines)}")
for l in lines[:100]:
    print(l)
if len(lines) > 100:
    print("... middle omitted ...")
    for l in lines[-60:]:
        print(l)

ssh.close()
