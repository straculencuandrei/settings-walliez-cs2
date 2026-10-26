import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl -u cs2 --since "30 minutes ago" --no-pager | grep -E -i "crash|fault|segv|watchdog|fatal|error|killed|dumped|core|stack" | tail -n 40
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== CRASH LOGS ===")
print(stdout.read().decode('utf-8', errors='ignore'))

script2 = """
coredumpctl list --since "30 minutes ago" --no-pager || true
"""
stdin, stdout, stderr = ssh.exec_command(script2)
print("=== COREDUMPS ===")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
