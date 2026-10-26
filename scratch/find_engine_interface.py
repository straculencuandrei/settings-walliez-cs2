import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
with open("/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so", "rb") as f:
    data = f.read()

import struct
target = struct.pack("<Q", 0x28db61)
for i in range(0, len(data), 8):
    if data[i:i+8] == target:
        print("Reference to Source2EngineToServer001 at:", hex(i))
        # The InterfaceReg struct: [next_ptr, create_func, name_ptr]
        # or [create_func, name_ptr]
        print("Previous 16 bytes:", [hex(struct.unpack("<Q", data[i-16+k*8:i-8+k*8])[0]) for k in range(2)])
        print("Next 16 bytes:", [hex(struct.unpack("<Q", data[i+8+k*8:i+16+k*8])[0]) for k in range(2)])
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
