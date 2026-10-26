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
# Use ilspycmd or monodis or strings
out = subprocess.check_output(["monodis", "--method", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll"], stderr=subprocess.STDOUT).decode("latin-1")
for line in out.splitlines():
    if "ExecuteClientCommand" in line:
        print(line)
' 2>/dev/null || true
"""
print(run(script))

ssh.close()
