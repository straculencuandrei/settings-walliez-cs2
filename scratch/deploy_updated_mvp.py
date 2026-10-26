import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

# Upload local Custom_MVP_Sounds.cs to server
sftp = ssh.open_sftp()
local_path = r'c:\Users\buzunar\Documents\cs2server\server-configs\plugins\Custom_MVP_Sounds\Custom_MVP_Sounds.cs'
remote_path = '/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs'
print(f"Uploading {local_path} -> {remote_path}")
sftp.put(local_path, remote_path)
sftp.close()

# Build and deploy
cmd = """
cd /home/csgoserver/cs2-custom-mvp
dotnet build -c Release
cp -f /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.* /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/
chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds/
systemctl restart cs2
sleep 3
systemctl status cs2 --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== BUILD & DEPLOY OUTPUT ===")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

ssh.close()
