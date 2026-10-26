import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_engine_dyn.py
import subprocess
out = subprocess.check_output(["nm", "-D", "-C", "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so"]).decode("latin-1")
for l in out.splitlines():
    if "ClientCommand" in l or "EngineServer" in l:
        print(l)
EOF
python3 /tmp/check_engine_dyn.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("OUT:", stdout.read().decode())
ssh.close()
