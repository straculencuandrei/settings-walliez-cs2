import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 300 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()

for i, l in enumerate(lines):
    if "Failed with result" in l or "status=11/SEGV" in l or "FATAL ERROR" in l:
        print("=== CRASH OCCURRENCE ===")
        for j in range(max(0, i-10), min(len(lines), i+5)):
            print(lines[j])

ssh.close()
