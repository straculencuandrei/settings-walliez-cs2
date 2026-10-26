import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_ecc.py
import subprocess
out = subprocess.check_output(["python3", "-c", '''
import clr
'''], stderr=subprocess.STDOUT)
EOF
python3 -c '
with open("/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll", "rb") as f:
    data = f.read()
import re
for m in re.finditer(b"ExecuteClientCommand", data):
    print("Found ExecuteClientCommand in API.dll at", hex(m.start()))
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
