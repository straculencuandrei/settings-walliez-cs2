import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.181.113.120', username='root', password=r')(e092e8EjTUiV')

# Upload cs2_crash_monitor.py
sftp = ssh.open_sftp()
local_path = r'c:\Users\buzunar\Documents\cs2server\scratch\cs2_crash_monitor.py'
remote_path = '/home/csgoserver/cs2_crash_monitor.py'
sftp.put(local_path, remote_path)
sftp.close()

# Make executable and install systemd unit
cmd = """
chmod +x /home/csgoserver/cs2_crash_monitor.py

cat << 'EOF' > /etc/systemd/system/cs2-crash-monitor.service
[Unit]
Description=CS2 Server Crash Monitor & Auto-Logger
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /home/csgoserver/cs2_crash_monitor.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now cs2-crash-monitor.service
systemctl status cs2-crash-monitor.service --no-pager
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== SETUP OUTPUT ===")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

ssh.close()
