import os, sys, paramiko, time

sys.stdout.reconfigure(encoding='utf-8')

print("[*] Connecting to remote server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV", timeout=15)
sftp = ssh.open_sftp()

# 1. Upload Helper.cs to server
print("[*] Uploading Helper.cs...")
with open("server-configs/plugins/Custom_MVP_Sounds/Config/Helper.cs", "r", encoding="utf-8") as f:
    helper_code = f.read()
with sftp.file("/home/csgoserver/cs2-custom-mvp/Config/Helper.cs", "w") as f:
    f.write(helper_code)

# 2. Upload Custom_MVP_Sounds.cs
print("[*] Uploading Custom_MVP_Sounds.cs...")
with open("server-configs/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.cs", "r", encoding="utf-8") as f:
    mvp_cs = f.read()
with sftp.file("/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.cs", "w") as f:
    f.write(mvp_cs)

# 3. Upload CustomMenu.cs
print("[*] Uploading CustomMenu.cs...")
with open("server-configs/plugins/CustomMenu/CustomMenu.cs", "r", encoding="utf-8") as f:
    cm_cs = f.read()
with sftp.file("/home/csgoserver/cs2-custommenu/CustomMenu.cs", "w") as f:
    f.write(cm_cs)

# 4. Remove temporary TestPoint.cs
ssh.exec_command("rm -f /home/csgoserver/cs2-custom-mvp/TestPoint.cs")

# 5. Build cs2-custom-mvp
print("[*] Building Custom_MVP_Sounds...")
stdin, stdout, stderr = ssh.exec_command("cd /home/csgoserver/cs2-custom-mvp && dotnet build -c Release")
out = stdout.read().decode('utf-8')
if "Build succeeded." not in out:
    print("[ERROR] Custom_MVP_Sounds build failed:\n", out)
    ssh.close()
    sys.exit(1)
print("[+] Custom_MVP_Sounds build succeeded!")

# 6. Build cs2-custommenu
print("[*] Building CustomMenu...")
stdin, stdout, stderr = ssh.exec_command("cd /home/csgoserver/cs2-custommenu && dotnet build -c Release")
out = stdout.read().decode('utf-8')
if "Build succeeded." not in out:
    print("[ERROR] CustomMenu build failed:\n", out)
    ssh.close()
    sys.exit(1)
print("[+] CustomMenu build succeeded!")

# 7. Deploy binaries
print("[*] Deploying binaries to plugin directories...")
mvp_plugin = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds"
cm_plugin = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/CustomMenu"

ssh.exec_command(f"cp /home/csgoserver/cs2-custom-mvp/bin/Release/net8.0/Custom_MVP_Sounds.* {mvp_plugin}/")
ssh.exec_command(f"cp /home/csgoserver/cs2-custommenu/bin/Release/net8.0/CustomMenu.* {cm_plugin}/")
ssh.exec_command(f"chown -R csgoserver:csgoserver {mvp_plugin} {cm_plugin} /home/csgoserver/cs2-custom-mvp /home/csgoserver/cs2-custommenu")

# 8. Download other Config files locally to keep repo complete
local_config_dir = "server-configs/plugins/Custom_MVP_Sounds/Config"
os.makedirs(local_config_dir, exist_ok=True)

for cf in ["Configs.cs", "Globals.cs", "mysql.cs"]:
    try:
        with sftp.file(f"/home/csgoserver/cs2-custom-mvp/Config/{cf}", "r") as rf:
            with open(os.path.join(local_config_dir, cf), "w", encoding="utf-8") as wf:
                wf.write(rf.read().decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"[-] Could not download {cf}: {e}")

try:
    with sftp.file("/home/csgoserver/cs2-custom-mvp/Custom_MVP_Sounds.csproj", "r") as rf:
        with open("server-configs/plugins/Custom_MVP_Sounds/Custom_MVP_Sounds.csproj", "w", encoding="utf-8") as wf:
            wf.write(rf.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print(f"[-] Could not download csproj: {e}")

try:
    with sftp.file("/home/csgoserver/cs2-custommenu/CustomMenu.csproj", "r") as rf:
        with open("server-configs/plugins/CustomMenu/CustomMenu.csproj", "w", encoding="utf-8") as wf:
            wf.write(rf.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print(f"[-] Could not download CustomMenu.csproj: {e}")

sftp.close()

# 9. Restart cs2 service
print("[*] Restarting cs2 service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

print("[*] Waiting 7 seconds for server & plugin startup...")
time.sleep(7)

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 40 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print("=== SERVER JOURNAL OUTPUT ===")
for l in lines:
    if any(k in l.lower() for k in ["custom_mvp", "custommenu", "error", "exception", "loaded plugin", "finished loading", "started"]):
        print("  ", l)

ssh.close()
print("[+] All fixes deployed successfully!")
