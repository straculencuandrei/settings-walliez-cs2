import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out + err

script = """
python3 -c '
import subprocess, re
pid = subprocess.check_output(["pidof", "cs2"]).decode().strip().split()[0]

maps = open(f"/proc/{pid}/maps").read()
m = re.search(r"^([0-9a-f]+)-[0-9a-f]+ r--p .*counterstrikesharp\\.so", maps, re.M)
base = int(m.group(1), 16)
engine_ptr_addr = base + 0x534df0
print(f"engine_ptr_addr: 0x{engine_ptr_addr:x}")

gdb_cmd = [
    "gdb", "-batch",
    "-p", pid,
    "-ex", f"set $engine = (void**)*(unsigned long*)0x{engine_ptr_addr:x}",
    "-ex", "p $engine",
    "-ex", "set $vtable = (void**)*$engine",
    "-ex", "p $vtable",
    "-ex", "x/1a ((char*)$vtable + 0x170)",
    "-ex", "disassemble *(void**)((char*)$vtable + 0x170), *(void**)((char*)$vtable + 0x170) + 40"
]
out = subprocess.check_output(gdb_cmd).decode("latin-1")
print(out)
'
"""
print(run(script))

ssh.close()
