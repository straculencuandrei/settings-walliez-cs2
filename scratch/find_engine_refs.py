import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_engine_interface.py
import subprocess
out = subprocess.check_output(["objdump", "-d", "-C", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so"]).decode("latin-1")
for line in out.splitlines():
    if "534df0" in line:
        print(line)
EOF
python3 /tmp/check_engine_interface.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("OUT:", stdout.read().decode())
ssh.close()
