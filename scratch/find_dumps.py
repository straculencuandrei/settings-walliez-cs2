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

print("=== core_pattern ===")
print(run('cat /proc/sys/kernel/core_pattern'))

print("=== find minidumps ===")
print(run('find /tmp /home/csgoserver -name "*.dmp" 2>/dev/null'))

ssh.close()
