# CS2 Server Settings & Custom MVP Workshop Suite

This repository contains the complete configuration, custom CounterStrikeSharp plugins, and the automated Steam Workshop MVP pipeline developed for the **Walliez CS2 Server**.

---

## 📁 Repository Structure

### 1. MVP Studio & Audio Pipeline
* **`wlz_mvp_studio.py` / `wlzMVP_Studio.bat`**: All-in-one studio tool for adding anthems, batch recompiling, and managing CS2 Workshop Tools.
* **`export_clean_mp3.py` / `Convert_To_Clean_44k_MP3.bat`**: Audio converter implementing the exact clean MP3 44.1 kHz, 320 kbps CBR, metadata-stripped algorithm with 10.0s trimming and a smooth 1-second fadeout.
* **`wlzMVP/`**: Complete source files for the Workshop Addon `wlzMVP` (Item ID: `3827657422`), including `soundevents_addon.vsndevts`, `addoninfo.txt`, preview thumbnails, and staged tracks.

### 2. Custom CounterStrikeSharp Plugins
* **`server-configs/plugins/Custom_MVP_Sounds/`**:
  * **`Custom_MVP_Sounds.cs`**: Modernized WASD-driven MVP Anthem selection menu (`/mvp`). Includes per-tick HUD rendering (no flickering/popping) and safe client-side playback.
  * **`MVP_Settings.json`**: Live server track definitions and configurations.
* **`server-configs/plugins/CustomMenu/`**:
  * **`CustomMenu.cs`**: WASD-driven `/menu` plugin with emoji-free clean styling and confirmation sub-menus.
  * **`CustomMenu.json`**: Menu definitions and command bindings.

### 3. Server Engine & Addon Configurations
* **`server-configs/cfg/multiaddonmanager.cfg`**: MultiAddonManager configuration mounting Workshop Addon `3827657422` for all connecting players.
* **`SERVER_DOCUMENTATION.md`**: Full documentation of server infrastructure, credentials, file paths, and operations.

### 4. Utilities & Automation (`scratch/`)
* **`pack_and_deploy_all.py`**: Automated packaging into monolithic VPK and direct SFTP sync to all server workshop locations.
* **`build_and_deploy_mvp_v3.py`**: Remote compilation of the C# plugin and automated server restart.

---

## 🛠️ Usage Quick Reference

### Add a New MVP Anthem
1. Drag and drop any `.mp3` or `.wav` onto **`wlzMVP_Studio.bat`** (or run `python wlz_mvp_studio.py`).
2. Enter the track display name and optional start time.
3. The script automatically exports clean 44.1 kHz audio, trims to 10 seconds with fadeout, regenerates KV3 soundevents, invokes Valve's `resourcecompiler.exe`, syncs the dedicated server config, and launches the CS2 Workshop Manager to submit the update.

### Convert Audio to Clean 44.1 kHz
Drag and drop any audio file onto **`Convert_To_Clean_44k_MP3.bat`** for a clean, stripped 10-second MP3 export.
