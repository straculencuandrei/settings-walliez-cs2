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
    print("server_mgr:", hex(server_mgr))

    f.seek(server_mgr + 0x150)
    net_server = struct.unpack("<Q", f.read(8))[0]
    print("net_server:", hex(net_server))

    f.seek(net_server + 0x268)
    client_count = struct.unpack("<i", f.read(4))[0]
    print("client_count (0x268):", client_count)

    f.seek(net_server + 0x270)
    client_arr = struct.unpack("<Q", f.read(8))[0]
    print("client_arr (0x270):", hex(client_arr))

    for i in range(min(5, max(1, client_count))):
        f.seek(client_arr + i * 8)
        c_ptr = struct.unpack("<Q", f.read(8))[0]
        print(f"Client {i}: {hex(c_ptr)}")
        if c_ptr:
            f.seek(c_ptr)
            c_vtable = struct.unpack("<Q", f.read(8))[0]
            print(f"   vtable: {hex(c_vtable)} (libengine2 + {hex(c_vtable - engine_base)})")
            f.seek(c_vtable + 0x80)
            send_net_msg = struct.unpack("<Q", f.read(8))[0]
            print(f"   SendNetMessage fn (+0x80): {hex(send_net_msg)}")
            for line in maps:
                parts = line.split()
                start, end = [int(x, 16) for x in parts[0].split("-")]
                if start <= send_net_msg < end:
                    print(f"   -> in library: {line.strip()}")
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
