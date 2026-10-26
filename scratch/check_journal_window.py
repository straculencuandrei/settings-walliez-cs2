import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl -u cs2 --since "15:30:00" --until "15:42:00" --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script)
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print(f"Total lines: {len(lines)}")
for l in lines[-60:]:
    print(l)

ssh.close()
