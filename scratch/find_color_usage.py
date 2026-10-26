import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
cat << 'EOF' > /tmp/inspect_dll.py
import subprocess

# Look for Color in other plugin sources
import glob
print("Searching for color in existing plugins:")
for f in glob.glob("/home/csgoserver/cs2-*/**/*.cs", recursive=True):
    with open(f, 'r', errors='ignore') as fp:
        for line in fp:
            if "ChatColors" in line or "Color" in line:
                if "{" in line or "PrintToChat" in line or "Replace" in line:
                    print(f"{f}: {line.strip()[:100]}")
                    break
EOF
python3 /tmp/inspect_dll.py
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
