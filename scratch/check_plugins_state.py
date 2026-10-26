import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print('=== GIT STATUS IN cs2-custom-mvp ===')
print(run('cd /home/csgoserver/cs2-custom-mvp && git status && git log -n 3 --oneline'))

print('=== INSTALLED PLUGIN DLL HASHES ===')
print(run('md5sum /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.dll 2>/dev/null || true'))

print('=== MENU MANAGER CORE FILES ===')
print(run('find /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/ -iname "*menu*"'))

ssh.close()
