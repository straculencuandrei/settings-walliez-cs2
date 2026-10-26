import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 2:
    print("Usage: python remote_exec.py <cmd>")
    sys.exit(1)

cmd = " ".join(sys.argv[1:])

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
if out:
    print(out, end='')
if err:
    print(err, file=sys.stderr, end='')

ssh.close()
