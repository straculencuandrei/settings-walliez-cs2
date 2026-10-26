import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
python3 -c '
path = "/home/csgoserver/cs2-custom-mvp/Config/Helper.cs"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
if "using CounterStrikeSharp.API.Core.Translations;" not in c:
    c = "using CounterStrikeSharp.API.Core.Translations;\\n" + c
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Added using")
else:
    print("Already present")
'
cd /home/csgoserver/cs2-custom-mvp && dotnet build -c Release
"""
stdin, stdout, stderr = ssh.exec_command(script)
print("=== BUILD RESULT ===")
print(stdout.read().decode('utf-8', errors='ignore'))
print("=== BUILD ERR ===")
print(stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
