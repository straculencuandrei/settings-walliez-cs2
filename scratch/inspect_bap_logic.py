import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["objdump", "-d", "-C", "/home/csgoserver/server-cs2/game/csgo/addons/multiaddonmanager/bin/multiaddonmanager.so"]).decode("latin-1")
idx = out.find("BuildAddonPath")
print(out[idx:idx+800])
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
