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

print("=== CSS logs list ===")
print(run('ls -lt /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/ | head -n 10'))

print("=== Latest CSS log content (tail) ===")
print(run('tail -n 60 /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/$(ls -t /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/ | head -n 1)'))

ssh.close()
