import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
import subprocess
pid = subprocess.check_output(["pgrep", "-u", "csgoserver", "cs2"]).decode().strip().split()[0]

first_base = None
with open(f"/proc/{pid}/maps") as f:
    for line in f:
        if "counterstrikesharp.so" in line:
            if first_base is None:
                first_base = int(line.split("-")[0], 16)
                print("First CSS mapping:", hex(first_base), line.strip())
            else:
                print("Mapping:", line.strip())

if first_base:
    addr = first_base + 0x536dd8
    with open(f"/proc/{pid}/mem", "rb") as mem:
        mem.seek(addr)
        target = int.from_bytes(mem.read(8), "little")
        print("Resolved CBaseEntity_EmitSoundFilter at", hex(addr), ":", hex(target))
        with open(f"/proc/{pid}/maps") as f:
            for l in f:
                parts = l.split()
                bounds = parts[0].split("-")
                start = int(bounds[0], 16)
                end = int(bounds[1], 16)
                if start <= target < end:
                    print("Function is in:", l.strip(), "offset in lib:", hex(target - start))
'
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
