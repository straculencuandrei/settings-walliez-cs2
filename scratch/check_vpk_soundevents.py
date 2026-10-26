import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

remote_code = """
import re

with open('/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422/3827657422.vpk', 'rb') as f:
    data = f.read()

strings = re.findall(rb'[a-zA-Z0-9_./\-]{4,}', data)
print("Found strings:")
seen = set()
for s in strings:
    s_str = s.decode('utf-8', errors='ignore')
    if any(k in s_str.lower() for k in ['mvp', 'vsnd', 'sound', 'gta', 'stiu']):
        if s_str not in seen:
            seen.add(s_str)
            print('  ', s_str)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_vpk2.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("python3 /tmp/check_vpk2.py")
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
