import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
echo "=== COREDUMP INFO ==="
coredumpctl info 33568 || true

echo "=== JOURNAL BETWEEN 16:41:20 and 16:41:46 ==="
journalctl -u cs2 --since "16:41:20" --until "16:41:46" --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
