import paramiko
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

remote_script = """python3 -c "
import re
with open('/home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422/3827657422_dir.vpk', 'rb') as f:
    data = f.read(200000)
for m in set(re.findall(b'[a-zA-Z0-9_/.-]+\\\\.(?:vsnd_c|vsndevts_c|vsnd)', data)):
    print(m.decode('latin1'))
"
"""

print(run(remote_script))
ssh.close()
