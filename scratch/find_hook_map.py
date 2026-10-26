import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
# get PID of cs2
import subprocess, struct
pid = subprocess.check_output(["pgrep", "-f", "cs2 -dedicated"]).decode().strip().split()[0]
with open(f"/proc/{pid}/maps") as f:
    maps = f.readlines()

engine_base = None
for line in maps:
    if "libengine2.so" in line and engine_base is None:
        engine_base = int(line.split("-")[0], 16)

with open(f"/proc/{pid}/mem", "rb") as f:
    f.seek(engine_base + 0xa9e6f0)
    server_mgr = struct.unpack("<Q", f.read(8))[0]
    f.seek(server_mgr + 0x150)
    net_server = struct.unpack("<Q", f.read(8))[0]
    f.seek(net_server + 0x270)
    client_arr = struct.unpack("<Q", f.read(8))[0]
    f.seek(client_arr)
    c_ptr = struct.unpack("<Q", f.read(8))[0]
    f.seek(c_ptr)
    c_vtable = struct.unpack("<Q", f.read(8))[0]
    f.seek(c_vtable + 0x80)
    send_net_msg = struct.unpack("<Q", f.read(8))[0]
    print("SendNetMessage trampoline:", hex(send_net_msg))

    # Read the target address called by trampoline:
    # at trampoline + 0x91: movabs $target, %rax
    f.seek(send_net_msg + 0x93)
    target = struct.unpack("<Q", f.read(8))[0]
    print("Target called by trampoline:", hex(target))

    for line in maps:
        parts = line.split()
        start, end = [int(x, 16) for x in parts[0].split("-")]
        if start <= target < end:
            print(f"Target is in: {line.strip()}, offset = {hex(target - start)}")
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
