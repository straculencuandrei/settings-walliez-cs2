import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print('=== CRASH MONITOR STATUS ===')
print(run('systemctl status cs2-crash-monitor.service --no-pager'))

print('=== LAST CRASH ===')
print(run('cat /home/csgoserver/LAST_CRASH.txt 2>/dev/null || echo "No crashes logged yet"'))

print('=== CS2 STATUS ===')
print(run('systemctl status cs2.service --no-pager | head -n 15'))

ssh.close()
