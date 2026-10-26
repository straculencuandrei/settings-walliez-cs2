import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
journalctl -u cs2 --since "12:00:00" --no-pager | grep -C 10 -i "stiu"
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== GREP STIU ===")
print(stdout.read().decode('utf-8', errors='ignore'))

script2 = """
journalctl -u cs2 --since "12:00:00" --no-pager | grep -C 10 -i "preview"
"""
stdin, stdout, stderr = ssh.exec_command(script2)
print("=== GREP PREVIEW ===")
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
