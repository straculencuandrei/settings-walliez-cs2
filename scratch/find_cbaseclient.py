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

script = """
python3 -c '
import subprocess
out = subprocess.check_output(["strings", "-t", "x", "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so"]).decode("latin-1")
for line in out.splitlines():
    if "CBaseClient" in line or "CGameClient" in line or "SendNetMsg" in line or "SendNetMessage" in line:
        print(line)
'
"""
print(run(script))

ssh.close()
