import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = """
python3 -c '
import subprocess
# find offset of string CPointClientCommand_API::Command at 0x97a060
out = subprocess.check_output(["python3", "-c", """
with open("/home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so", "rb") as f:
    data = f.read()
import struct
# search for reference to 0x97a060 or search for CPointClientCommand
pos = 0
found = []
import re
# look for xref to 0x97a060 or search string in .rodata
"""])
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
