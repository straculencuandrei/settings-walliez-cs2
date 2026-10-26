import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
# get PID of cs2
import subprocess, struct
pid = subprocess.check_output(["pgrep", "-f", "cs2 -dedicated"]).decode().strip().split()[0]

# Check strings in libengine2.so for "play " or find ConCommand "play"
out = subprocess.check_output(["gdb", "-batch", "-ex", "file /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so", "-ex", "info address __cmd_play"]).decode("latin-1")
print(out)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
