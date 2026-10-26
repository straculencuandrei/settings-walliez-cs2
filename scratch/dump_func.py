import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["objdump", "-d", "-C", "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libsoundsystem.so"]).decode("latin-1")
idx1 = out.find("278100:")
if idx1 == -1: idx1 = out.find("2781")
idx2 = out.find("278600:")
if idx2 == -1: idx2 = out.find("2786")
print(out[idx1:idx2])
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
