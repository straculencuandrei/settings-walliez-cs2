import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

remote_code = """
with open('/home/csgoserver/cs2-custommenu/CustomMenu.cs', 'r') as f:
    lines = f.readlines()
    for i, l in enumerate(lines):
        if 'EmitSound' in l:
            for j in range(max(0, i-10), min(len(lines), i+15)):
                print(f"{j+1}: {lines[j].rstrip()}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_emit.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("python3 /tmp/check_emit.py")
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
