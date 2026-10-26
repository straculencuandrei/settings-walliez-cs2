import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

# Let's inspect MenuManager in CounterStrikeSharp.API.dll using python-based reflection or strings
print('=== CounterStrikeSharp Menu Types ===')
cmd = """python3 -c "
import subprocess
out = subprocess.check_output(['monodis', '--assemblyref', '/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll'], stderr=subprocess.STDOUT).decode('utf-8', errors='ignore')
print(out[:500])
" 2>/dev/null || true"""
print(run(cmd))

# Let's search strings for CenterHtmlMenu methods
print('=== CenterHtmlMenu strings ===')
print(run("strings /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll | grep -E 'CenterHtmlMenu|MenuManager' | head -n 30"))

ssh.close()
