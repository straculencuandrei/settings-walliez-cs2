#!/usr/bin/env python3
"""
CS2 MVP Anthem Local Client Synchronizer
-----------------------------------------
Syncs custom MVP Anthems from the dedicated server's FastDL mirror directly into your local CS2 game files.
Works on Windows across any Steam library drive.
"""

import os
import re
import sys
import urllib.request
import urllib.error

FASTDL_BASE = "http://81.181.113.120/fastdl"

STEAM_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
    r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
    r"E:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
    r"D:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
    r"E:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
    r"C:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo"
]

def find_local_cs2():
    for p in STEAM_PATHS:
        if os.path.exists(p):
            return p
    return None

def sync():
    print("=" * 60)
    print("        CS2 MVP Anthem 1-Click Client Sync")
    print("=" * 60)

    cs2_dir = find_local_cs2()
    if not cs2_dir:
        print("[X] Could not locate your Counter-Strike 2 installation directory.")
        print("    Please ensure CS2 is installed via Steam.")
        return 1

    print(f"[*] Detected CS2 directory: {cs2_dir}")

    # Discover tracks from FastDL HTML listing
    tracks = []
    try:
        url = f"{FASTDL_BASE}/sounds/mvp/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'href="([^"?#/]+\.mp3)"', html)
            tracks = list(dict.fromkeys(matches))
    except Exception as e:
        print(f"[!] Warning fetching track directory index: {e}")

    # Fallback default tracks if index was empty
    if not tracks:
        tracks = ["flawless.mp3", "florinsalam.mp3", "stiu_feat_walli3z_mastered.mp3"]

    print(f"[*] Found {len(tracks)} MVP anthems on server.")

    dest_dirs = [
        os.path.join(cs2_dir, 'sounds', 'mvp'),
        os.path.join(cs2_dir, 'sound', 'mvp')
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)

    synced_count = 0
    for track in tracks:
        track_url = f"{FASTDL_BASE}/sounds/mvp/{track}"
        print(f"[*] Downloading {track} ...")
        try:
            req = urllib.request.Request(track_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()

            for d in dest_dirs:
                with open(os.path.join(d, track), 'wb') as f:
                    f.write(data)

            print(f"    [+] Saved {track} ({len(data) / 1024:.1f} KB)")
            synced_count += 1
        except Exception as ex:
            print(f"    [!] Failed to download {track}: {ex}")

    print("\n" + "=" * 60)
    print(f"[SUCCESS] {synced_count} MVP Anthems are synced to your CS2 game files!")
    print("All custom MVP Anthems will now play out loud in game.")
    print("=" * 60 + "\n")
    return 0

if __name__ == '__main__':
    sys.exit(sync())
