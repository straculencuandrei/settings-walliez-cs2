import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

remote_script = """
python3 -c "
with open('/home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so', 'rb') as f:
    data = f.read()

sig = bytes.fromhex('55 48 89 E5 53 48 89 FB 48 83 EC')
pos = 0
found = []
while True:
    pos = data.find(sig, pos)
    if pos == -1: break
    found.append(pos)
    pos += 1

print('Found matches:', [hex(p) for p in found])
for p in found:
    print('Disasm at', hex(p))
    import subprocess
    print(subprocess.getoutput(f'objdump -d --start-address={p} --stop-address={p+64} /home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so'))
"
"""
stdin, stdout, stderr = ssh.exec_command(remote_script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
