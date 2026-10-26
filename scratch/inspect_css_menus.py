import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print('=== INSPECTING CounterStrikeSharp Menu Classes ===')
script = run('''python3 -c "
import subprocess
out = subprocess.check_output(['strings', '/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/WeaponPaints/CounterStrikeSharp.API.dll']).decode('utf-8', errors='ignore')
for line in out.splitlines():
    if 'Menu' in line and any(k in line for k in ['CenterHtml', 'ChatMenu', 'ConsoleMenu', 'Open']):
        print(line)
"''')
print(script[:1000])

ssh.close()
