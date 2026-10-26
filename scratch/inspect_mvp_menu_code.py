import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace')

print('=== Custom_MVP_Sounds.cs (Menu rendering & Tick logic) ===')
script = run('''python3 -c "
with open('/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if any(k in l for k in ['PrintToCenterHtml', 'OnTick', 'RenderMenu', 'OpenMenu', 'HandleKeyPress', 'Buttons', 'PlaySound', 'Preview']):
        print(f'{i+1}: {l}', end='')
"''')
print(script)

ssh.close()
