import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

cmd = 'gdb -batch -ex "file /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/libengine2.so" -ex "disassemble 0x538ed0,0x538f50"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
ssh.close()
