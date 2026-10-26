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
import subprocess
gdb_cmd = [
    "gdb", "-batch",
    "-ex", "file /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so",
    "-ex", "disassemble _ZN18counterstrikesharpL18IssueClientCommandERNS_13ScriptContextE",
    "-ex", "disassemble _ZN18counterstrikesharpL28IssueClientCommandFromServerERNS_13ScriptContextE"
]
out = subprocess.check_output(gdb_cmd).decode("latin-1")
print(out)
'
"""
print(run(script))

ssh.close()
