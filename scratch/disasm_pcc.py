import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
out = subprocess.check_output(["nm", "-D", "-C", "/home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so"]).decode("latin-1")
for line in out.splitlines():
    if "PointClientCommand" in line or "point_clientcommand" in line:
        print(line)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
print("ERR:", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
