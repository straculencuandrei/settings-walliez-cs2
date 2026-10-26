import os, sys, paramiko, time

sys.stdout.reconfigure(encoding='utf-8')

print("[*] Reading updated Custom_MVP_Sounds_WASD.cs...")
with open("scratch/Custom_MVP_Sounds_WASD.cs", "r", encoding="utf-8") as f:
    main_cs = f.read()

print("[*] Connecting to remote server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV", timeout=15)

src_dir = "/home/csgoserver/cs2-custom-mvp"
plugin_dir = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds"

sftp = ssh.open_sftp()
with sftp.file(f"{src_dir}/Custom_MVP_Sounds.cs", "w") as f:
    f.write(main_cs)
sftp.close()

print("[*] Compiling Custom_MVP_Sounds on remote server...")
stdin, stdout, stderr = ssh.exec_command(f"cd {src_dir} && dotnet build -c Release")
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print(out)
if "Build succeeded." not in out:
    print("[ERROR] Build failed:\n", err)
    ssh.close()
    sys.exit(1)

print("[*] Deploying compiled binaries to plugin directory...")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.dll {plugin_dir}/Custom_MVP_Sounds.dll")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.deps.json {plugin_dir}/Custom_MVP_Sounds.deps.json")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.pdb {plugin_dir}/Custom_MVP_Sounds.pdb")
ssh.exec_command(f"chown -R csgoserver:csgoserver {plugin_dir} {src_dir}")

print("[*] Restarting cs2 service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

print("[*] Waiting 5 seconds for plugin load...")
time.sleep(5)

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 25 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
for l in lines:
    if "Custom_MVP_Sounds" in l or "Custom MVP" in l or "error" in l.lower() or "exception" in l.lower():
        print("  ", l)

ssh.close()
print("[+] Custom_MVP_Sounds deployed successfully!")
