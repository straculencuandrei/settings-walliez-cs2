import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = 'gdb -batch -ex "file /home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/bin/linuxsteamrt64/counterstrikesharp.so" -ex "x/s 0x401aaa"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
ssh.close()
