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
sed -i 's/"version": "8.0.0"/"version": "10.0.0"/' /tmp/net10_test/bin/Release/net8.0/net10_test.runtimeconfig.json
/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/dotnet/dotnet /tmp/net10_test/bin/Release/net8.0/net10_test.dll
"""
print(run(script))

ssh.close()
