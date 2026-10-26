import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

stdin, stdout, stderr = ssh.exec_command("ls -t /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/ | head -5")
latest_files = stdout.read().decode().splitlines()
print("Latest log files:", latest_files)
if latest_files:
    cmd = f"tail -n 50 /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs/{latest_files[0]}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
ssh.close()
