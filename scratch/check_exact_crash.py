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

cmd = r'''journalctl -u cs2 --since "2026-10-26 16:40:40" --until "2026-10-26 16:41:40" --no-pager'''
lines = run(cmd).splitlines()
for l in lines:
    if "recv queue overflow" not in l:
        print(l)

ssh.close()
