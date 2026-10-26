import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
echo "=== COREDUMP LIST ==="
coredumpctl list --no-pager | tail -n 10

echo "=== RECENT CRASH IN JOURNAL ==="
journalctl -u cs2 -n 80 --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
