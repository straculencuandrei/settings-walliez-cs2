import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV")

script = """
coredumpctl gdb 33568 --batch -ex "thread apply all bt 25" > /tmp/bt_33568.txt 2>&1 || true
head -n 60 /tmp/bt_33568.txt
echo "--- Searching for active threads ---"
grep -n "Thread " /tmp/bt_33568.txt | head -n 30
"""
stdin, stdout, stderr = ssh.exec_command(script)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()
