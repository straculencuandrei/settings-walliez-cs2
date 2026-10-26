import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl _PID=33568 --no-pager | tail -n 50
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== PID 33568 LAST LINES ===")
print(stdout.read().decode('utf-8', errors='ignore'))

script2 = """
journalctl -u cs2 --since "16:41:30" --until "16:41:45" --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script2)
print("=== SYSTEMD SERVICE LINES ===")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
