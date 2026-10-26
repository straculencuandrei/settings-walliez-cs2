import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

# Check CustomMenu.cs lines around EmitSound
stdin, stdout, stderr = ssh.exec_command("grep -C 5 'EmitSound' /home/csgoserver/cs2-custommenu/CustomMenu.cs")
print("CustomMenu EmitSound:\n", stdout.read().decode('utf-8', errors='ignore'))

# Check if other plugins use EmitSound
stdin, stdout, stderr = ssh.exec_command("find /home/csgoserver/ -name '*.cs' | xargs grep -n 'EmitSound' 2>/dev/null")
print("All EmitSound in CS files:\n", stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
