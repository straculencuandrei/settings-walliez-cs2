import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["strings", "-a", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so"]).decode("latin-1")
for line in out.splitlines():
    if "Source2EngineToClient" in line or "Source2EngineToServer" in line or "IVEngineServer" in line:
        print(line)
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
