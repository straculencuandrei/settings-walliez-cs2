import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
for addr in [0x1f775c0, 0x22147a0]:
    print("=== Address:", hex(addr), "===")
    cmd = f"objdump -d -C --start-address={addr} --stop-address={addr+120} /home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so"
    print(subprocess.getoutput(cmd))
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
