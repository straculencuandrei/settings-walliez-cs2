import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
out = subprocess.check_output(["gdb", "-batch", "-ex", "file /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so", "-ex", "disassemble 0x176490"]).decode("latin-1")
print(out)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
