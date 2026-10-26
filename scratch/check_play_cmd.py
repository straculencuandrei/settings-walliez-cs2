import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["gdb", "-batch", "-ex", "file /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so", "-ex", "info address __command_play"]).decode("latin-1")
print(out)
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
