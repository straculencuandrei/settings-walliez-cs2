import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu/config.json || true
cat /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu/lang/en.json || true
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
