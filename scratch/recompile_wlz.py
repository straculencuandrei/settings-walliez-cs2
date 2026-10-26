import subprocess, shutil, os

src_wav = r"C:\Users\buzunar\Documents\cs2server\wlzMVP\sounds\mvp\stiufeatWALLI3Zmastered.wav"
dst_wav = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP\sounds\mvp\stiufeatWALLI3Zmastered.wav"

shutil.copyfile(src_wav, dst_wav)
print(f"Copied WAV ({os.path.getsize(dst_wav)} bytes)")

compiler = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\resourcecompiler.exe"
content_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP"

cmd = [compiler, "-r", "-f", "-i", f"{content_dir}\\*.*"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Compiler STDOUT:", res.stdout)
if res.stderr:
    print("Compiler STDERR:", res.stderr)

vsnd_c = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\wlzMVP\sounds\mvp\stiufeatwalli3zmastered.vsnd_c"
if os.path.exists(vsnd_c):
    print(f"[+] Recompiled vsnd_c size: {os.path.getsize(vsnd_c)} bytes")
