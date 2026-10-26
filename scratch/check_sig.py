import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
with open("/home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so", "rb") as f:
    data = f.read()

sig = bytes.fromhex("55 48 89 E5 53 48 89 FB 48 83 EC")
pos = 0
while True:
    pos = data.find(sig, pos)
    if pos == -1: break
    # check if followed by E8
    if data[pos+12] == 0xe8 and data[pos+17] == 0x48 and data[pos+18] == 0x89 and data[pos+19] == 0xd8:
        print("MATCH at offset:", hex(pos))
        import subprocess
        print(subprocess.getoutput(f"objdump -d --start-address={pos} --stop-address={pos+40} /home/csgoserver/server-cs2/game/csgo/bin/linuxsteamrt64/libserver.so"))
    pos += 1
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
