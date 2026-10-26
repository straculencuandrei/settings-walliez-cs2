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

print("=== MD5 of deployed plugin DLL ===")
print(run('md5sum /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.dll'))

print("=== MD5 of compiled DLL in cs2-custom-mvp ===")
print(run('md5sum /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.dll 2>/dev/null || true'))

print("=== Git status or last modified time of Custom_MVP_Sounds.cs ===")
print(run('ls -la /home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs'))

ssh.close()
