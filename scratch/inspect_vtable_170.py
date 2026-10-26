import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/check_engine_slot.py
import subprocess

pid = subprocess.check_output(["pgrep", "-u", "csgoserver", "cs2"]).decode().strip().split()[0]

css_base = None
with open(f"/proc/{pid}/maps") as f:
    for line in f:
        if "counterstrikesharp.so" in line and "r--p" in line and "00401000" in line:
            css_data_base = int(line.split("-")[0], 16) - 0x401000
            break
        elif "counterstrikesharp.so" in line and css_base is None:
            css_base = int(line.split("-")[0], 16)

print("CSS base:", hex(css_base))
engine_ptr_addr = css_base + 0x534df0
with open(f"/proc/{pid}/mem", "rb") as mem:
    mem.seek(engine_ptr_addr)
    engine_obj = int.from_bytes(mem.read(8), "little")
    print("Engine obj:", hex(engine_obj))
    mem.seek(engine_obj)
    vtable = int.from_bytes(mem.read(8), "little")
    print("Engine vtable:", hex(vtable))
    mem.seek(vtable + 0x170)
    slot_func = int.from_bytes(mem.read(8), "little")
    print("Func at vtable + 0x170:", hex(slot_func))

# Find library and symbol
with open(f"/proc/{pid}/maps") as f:
    for line in f:
        parts = line.split()
        bounds = parts[0].split("-")
        s, e = int(bounds[0], 16), int(bounds[1], 16)
        if s <= slot_func < e:
            print("Belongs to mapping:", line.strip())
            offset = slot_func - s
            lib = parts[-1]
            print(f"Offset in {lib}: {hex(offset)}")
            # Disassemble 30 instructions
            out = subprocess.check_output(["gdb", "-batch", "-ex", f"file {lib}", "-ex", f"disassemble {hex(offset)},{hex(offset+80)}"]).decode("latin-1")
            print("Disassembly:")
            print(out)
            break
EOF
python3 /tmp/check_engine_slot.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
