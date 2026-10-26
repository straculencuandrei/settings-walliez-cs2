import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

# Look at 0x24c380 or search for the instruction: 48 3b 83 88 00 00 00
cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["objdump", "-d", "-C", "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libsoundsystem.so"]).decode("latin-1")
idx = out.find("3b 83 88 00 00 00")
if idx != -1:
    print(out[max(0, idx-500):idx+300])
else:
    print("pattern not found")
'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
