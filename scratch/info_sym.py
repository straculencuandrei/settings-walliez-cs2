import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

script = """
python3 -c '
import subprocess
pid = subprocess.check_output(["pidof", "cs2"]).decode().strip().split()[0]
gdb_cmd = [
    "gdb", "-batch",
    "-p", pid,
    "-ex", "info symbol 0x704ec5471918",
    "-ex", "disassemble 0x704ec4f3a090, 0x704ec4f3a140"
]
out = subprocess.check_output(gdb_cmd).decode("latin-1")
print(out)
'
"""
print(run(script))

ssh.close()
