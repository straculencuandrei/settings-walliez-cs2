import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/decompile_ecc.py
import subprocess
try:
    out = subprocess.check_output(["monodis", "--method", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll"], stderr=subprocess.STDOUT)
    lines = out.decode("latin1").splitlines()
    for i, l in enumerate(lines):
        if "ExecuteClientCommand" in l:
            for j in range(max(0, i-5), min(len(lines), i+25)):
                print(lines[j])
except Exception as e:
    print("monodis failed:", e)
EOF
python3 /tmp/decompile_ecc.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
