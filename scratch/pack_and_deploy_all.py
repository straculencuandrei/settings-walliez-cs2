import os, sys, tempfile, shutil, paramiko, time, vpk

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("[*] 1. Creating Complete VPK with All Anthems...")
print("=" * 60)

src_addon = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\wlzMVP"
staging = tempfile.mkdtemp(prefix="vpk_stage_")

os.makedirs(os.path.join(staging, "sounds", "mvp"), exist_ok=True)
os.makedirs(os.path.join(staging, "soundevents"), exist_ok=True)

# Copy all compiled sound assets
sounds_dir = os.path.join(src_addon, "sounds", "mvp")
for f in os.listdir(sounds_dir):
    if f.endswith(".vsnd_c"):
        src_path = os.path.join(sounds_dir, f)
        dst_path = os.path.join(staging, "sounds", "mvp", f)
        shutil.copyfile(src_path, dst_path)
        print(f" - Included track: {f} ({os.path.getsize(src_path):,} bytes)")

# Copy soundevents
se_file = os.path.join(src_addon, "soundevents_addon.vsndevts_c")
if os.path.exists(se_file):
    shutil.copyfile(se_file, os.path.join(staging, "soundevents_addon.vsndevts_c"))
    shutil.copyfile(se_file, os.path.join(staging, "soundevents", "soundevents_addon.vsndevts_c"))
    print(f" - Included soundevents: soundevents_addon.vsndevts_c")

addoninfo_file = os.path.join(src_addon, "addoninfo.txt")
if os.path.exists(addoninfo_file):
    shutil.copyfile(addoninfo_file, os.path.join(staging, "addoninfo.txt"))
    print(f" - Included addoninfo.txt")

out_vpk = r"C:\Users\buzunar\Documents\cs2server\scratch\3827657422.vpk"
pak = vpk.new(staging)
pak.save(out_vpk)
vpk_size = os.path.getsize(out_vpk)
print(f"[+] Complete Monolithic VPK generated: {out_vpk} ({vpk_size:,} bytes)")
shutil.rmtree(staging)

# Also check CS2 workshop output directory
cs2_vpk_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\vpks\3827657422"
has_cs2_vpks = os.path.exists(cs2_vpk_dir) and os.path.exists(os.path.join(cs2_vpk_dir, "3827657422_dir.vpk"))

print("\n" + "=" * 60)
print("[*] 2. Connecting to CS2 Server (81.181.113.120)...")
print("=" * 60)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("81.181.113.120", port=22, username="root", password=")(e092e8EjTUiV", timeout=15)

# Deploy VPKs to all workshop paths on server
dest_dirs = [
    "/home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop/content/730/3827657422",
    "/home/csgoserver/server-cs2/steamapps/workshop/content/730/3827657422",
    "/home/csgoserver/Steam/steamapps/workshop/content/730/3827657422"
]

sftp = ssh.open_sftp()
for d in dest_dirs:
    ssh.exec_command(f"mkdir -p {d}")
    print(f"Uploading 3827657422.vpk -> {d}/3827657422.vpk...")
    sftp.put(out_vpk, f"{d}/3827657422.vpk")
    sftp.put(out_vpk, f"{d}/3827657422_000.vpk")

    if has_cs2_vpks:
        for fname in ["3827657422_dir.vpk", "3827657422_000.vpk"]:
            loc = os.path.join(cs2_vpk_dir, fname)
            if os.path.exists(loc):
                sftp.put(loc, f"{d}/{fname}")

print("[+] All workshop packages synchronized on server!")

print("\n" + "=" * 60)
print("[*] 3. Building and Deploying Custom_MVP_Sounds (WASD + Fixes)...")
print("=" * 60)

src_dir = "/home/csgoserver/cs2-custom-mvp"
plugin_dir = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/plugins/Custom_MVP_Sounds"

with open("scratch/Custom_MVP_Sounds_WASD.cs", "r", encoding="utf-8") as f:
    main_cs = f.read()

with sftp.file(f"{src_dir}/Custom_MVP_Sounds.cs", "w") as f:
    f.write(main_cs)
sftp.close()

# Compile plugin
stdin, stdout, stderr = ssh.exec_command(f"cd {src_dir} && dotnet build -c Release")
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print(out)
if "Build succeeded." not in out:
    print("[ERROR] Build failed:\n", err)
    ssh.close()
    sys.exit(1)

# Copy dll
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.dll {plugin_dir}/Custom_MVP_Sounds.dll")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.deps.json {plugin_dir}/Custom_MVP_Sounds.deps.json")
ssh.exec_command(f"cp {src_dir}/bin/Release/net8.0/Custom_MVP_Sounds.pdb {plugin_dir}/Custom_MVP_Sounds.pdb")

# Set permissions
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/game/bin/linuxsteamrt64/steamapps/workshop")
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/server-cs2/steamapps/workshop")
ssh.exec_command("chown -R csgoserver:csgoserver /home/csgoserver/Steam/steamapps/workshop")
ssh.exec_command(f"chown -R csgoserver:csgoserver {plugin_dir} {src_dir}")

print("\n" + "=" * 60)
print("[*] 4. Restarting CS2 Dedicated Server...")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command("systemctl restart cs2")
stdout.channel.recv_exit_status()

print("[*] Waiting 6 seconds for server and plugin startup...")
time.sleep(6)

stdin, stdout, stderr = ssh.exec_command("journalctl -u cs2 -n 35 --no-pager")
lines = stdout.read().decode('utf-8', errors='ignore').splitlines()
print("\n--- Recent Server Startup Logs ---")
for l in lines:
    if any(k in l.lower() for k in ['custom_mvp', 'custom mvp', 'addon', 'mount', 'mirage', 'started', 'error']):
        print("  ", l)

ssh.close()
print("\n[SUCCESS] Full deployment, compilation, and server restart complete!")
