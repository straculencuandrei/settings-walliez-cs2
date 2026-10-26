import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/disasm_engine_cc.py
import subprocess

pid = subprocess.check_output(["pgrep", "-u", "csgoserver", "cs2"]).decode().strip().split()[0]

# Find engine pointer from CSS
with open(f"/proc/{pid}/maps") as f:
    for line in f:
        if "counterstrikesharp.so" in line and "r-xp" in line:
            css_base = int(line.split("-")[0], 16)
            break

engine_ptr_addr = css_base + 0x534df0
with open(f"/proc/{pid}/mem", "rb") as mem:
    mem.seek(engine_ptr_addr)
    engine_obj = int.from_bytes(mem.read(8), "little")
    print("Engine object:", hex(engine_obj))
    mem.seek(engine_obj)
    vtable = int.from_bytes(mem.read(8), "little")
    print("Engine vtable:", hex(vtable))
    mem.seek(vtable + 0x170)
    slot_170_func = int.from_bytes(mem.read(8), "little")
    print("Slot 0x170 func:", hex(slot_170_func))

# Find which library slot_170_func belongs to
with open(f"/proc/{pid}/maps") as f:
    for line in f:
        parts = line.split()
        bounds = parts[0].split("-")
        s, e = int(bounds[0], 16), int(bounds[1], 16)
        if s <= slot_170_func < e:
            print("Belongs to:", line.strip(), "offset:", hex(slot_170_func - s))
            offset = slot_170_func - s
            lib = parts[-1]
            break

# Disassemble with gdb
out = subprocess.check_output(["gdb", "-batch", "-ex", f"file {lib}", "-ex", f"disassemble {hex(offset)},{hex(offset+200)}"]).decode("latin-1")
print("=== Disassembly of slot 0x170 ===")
print(out)
EOF
python3 /tmp/disasm_engine_cc.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
