import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

# Check how CustomMenu.cs compiled on the server
stdin, stdout, stderr = ssh.exec_command("grep -n 'EmitSound' /home/csgoserver/cs2-custommenu/CustomMenu.cs")
print("CustomMenu EmitSound line:\n", stdout.read().decode('utf-8', errors='ignore'))

# Check CSSharp dll with javap or monodis or dotnet
cmd = """
python3 -c '
import subprocess
out = subprocess.check_output(["monodis", "--typedef", "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/api/CounterStrikeSharp.API.dll"]).decode("latin-1") if False else ""
' 2>/dev/null || true
"""
stdin, stdout, stderr = ssh.exec_command(cmd)

ssh.close()
