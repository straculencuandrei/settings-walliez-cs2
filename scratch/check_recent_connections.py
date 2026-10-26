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

cmd = r'''journalctl -u cs2 --since "2026-10-26 16:42:00" --no-pager | grep -iE "doggg|steamid|client|connect|preview|mvp" | head -n 40'''
print(run(cmd))

ssh.close()
