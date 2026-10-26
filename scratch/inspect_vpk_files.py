import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print('=== VPK File Size and Strings ===')
print(run("ls -lh /home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422/"))
print(run("strings /home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422/3827657422_dir.vpk | head -n 30"))

ssh.close()
