import subprocess, os

kv3_content = """<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
    "CustomMVP.stiufeatwalli3zmastered" =
    {
        type = "csgo_music"
        volume = 1.000000
        pitch = 1.000000
        vsnd_files = [ "sounds/mvp/stiufeatwalli3zmastered.vsnd" ]
    }
    "CustomMVP.gta_iii_full_theme_hq" =
    {
        type = "csgo_music"
        volume = 1.000000
        pitch = 1.000000
        vsnd_files = [ "sounds/mvp/gta_iii_full_theme_hq.vsnd" ]
    }
}
"""

paths = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP\soundevents_addon.vsndevts",
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP\soundevents\soundevents_addon.vsndevts",
    r"C:\Users\buzunar\Documents\cs2server\wlzMVP\soundevents_addon.vsndevts",
    r"C:\Users\buzunar\Documents\cs2server\wlzMVP\soundevents\soundevents_addon.vsndevts",
]

for p in paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(kv3_content)
    print("Updated:", p)

compiler = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\resourcecompiler.exe"
content_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\content\csgo_addons\wlzMVP"

cmd = [compiler, "-r", "-f", "-i", f"{content_dir}\\*.*"]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
