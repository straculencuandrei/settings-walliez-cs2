import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
echo "=== CURRENT PROCESS ==="
ps aux | grep cs2 | grep -v grep

echo "=== JOURNAL AFTER 16:41:20 ==="
journalctl -u cs2 --since "16:41:00" --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
