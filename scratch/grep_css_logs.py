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

cmd = r'''grep -E "16:4[0-2]:" /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/log-all20261026.txt | head -n 40'''
print(run(cmd))

cmd_err = r'''grep -iE "exception|error|fatal|crash" /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/log-all20261026.txt | tail -n 30'''
print("=== Errors in log-all ===")
print(run(cmd_err))

ssh.close()
