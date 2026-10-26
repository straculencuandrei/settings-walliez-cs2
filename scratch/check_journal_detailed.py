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

# Check logs since 17:10:00 excluding TEST_CRASH spam
cmd = r'''journalctl -u cs2 --since "2026-10-26 17:10:00" --no-pager | grep -v "TEST_CRASH" | grep -v "0 bytes" | tail -n 120'''
print(run(cmd))

ssh.close()
