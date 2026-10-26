import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
out = subprocess.check_output(["strings", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/core/CounterStrikeSharp.API.dll"])
lines = [l for l in out.decode("latin1").splitlines() if "{" in l and "}" in l]
print("Found potential color tags:")
for l in lines[:50]:
    if len(l) < 25:
        print(l)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
