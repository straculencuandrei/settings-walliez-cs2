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

cmd = r'''grep -rn "mvp" /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/'''
print("=== Matches in configs ===")
print(run(cmd))

cmd2 = r'''grep -rn "mvp" /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/*/'''
print("=== Matches in plugins ===")
print(run(cmd2))

ssh.close()
