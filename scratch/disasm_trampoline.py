import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
pid = subprocess.check_output(["pgrep", "-f", "cs2 -dedicated"]).decode().strip().split()[0]
out = subprocess.check_output(["gdb", "-batch", "-p", pid, "-ex", "x/25i 0x774d364d8869"]).decode("latin-1")
print(out)
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
