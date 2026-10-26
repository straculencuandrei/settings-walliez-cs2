import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 2000 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()

for i, l in enumerate(lines):
    if "33568" in l and ("WatchDog" in l or "status=11" in l or "FATAL ERROR" in l):
        print("=== CRASH OCCURRENCE 33568 ===")
        for j in range(max(0, i-60), min(len(lines), i+15)):
            print(lines[j])
        break

ssh.close()
