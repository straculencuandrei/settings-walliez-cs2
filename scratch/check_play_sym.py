import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_play_sym.py
import subprocess

pid = subprocess.check_output(["pgrep", "-u", "csgoserver", "cs2"]).decode().strip().split()[0]

out = subprocess.check_output(["gdb", "-batch", "-p", pid, "-ex", "info address __command_play", "-ex", "disassemble __command_play"]).decode("latin-1")
print(out)
EOF
python3 /tmp/check_play_sym.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
