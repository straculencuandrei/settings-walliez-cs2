import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl _PID=33568 --no-pager | tail -n 25
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== PID 33568 LAST 25 LINES ===")
print(stdout.read().decode('utf-8', errors='ignore'))

script2 = """
journalctl -u cs2 --since "16:41:20" --until "16:41:43" --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(script2)
print("=== SERVICE 16:41:20 to 16:41:43 ===")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
