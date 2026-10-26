import paramiko, sys
sys.stdout.reconfigure(encoding='utf-8')

cmd = sys.argv[1] if len(sys.argv) > 1 else "uptime"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
if out:
    print(out)
if err:
    print("ERR:", err)
ssh.close()
