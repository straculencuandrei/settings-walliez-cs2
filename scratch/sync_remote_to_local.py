import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

# Fetch the remote Custom_MVP_Sounds.cs and save locally
sftp = ssh.open_sftp()
with sftp.file('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs', 'r') as f_rem:
    content = f_rem.read().decode('utf-8')

with open('c:/Users/buzunar/Documents/cs2server/Custom_MVP_Sounds.cs', 'w', encoding='utf-8') as f_loc:
    f_loc.write(content)

print(f"Downloaded updated Custom_MVP_Sounds.cs ({len(content)} bytes)")

# Also download MVP_Settings.json
with sftp.file('/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/config/MVP_Settings.json', 'r') as f_rem:
    mvp_cfg = f_rem.read().decode('utf-8')
with open('c:/Users/buzunar/Documents/cs2server/MVP_Settings.json', 'w', encoding='utf-8') as f_loc:
    f_loc.write(mvp_cfg)

sftp.close()
ssh.close()
