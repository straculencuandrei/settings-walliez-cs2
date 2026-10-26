import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
with open("/home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so", "rb") as f:
    data = f.read()

# search for string "CPointClientCommand"
import subprocess
out = subprocess.check_output(["gdb", "-batch", "-ex", "file /home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so", "-ex", "x/30i 0x18564a0"]).decode("latin-1")
print(out)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
