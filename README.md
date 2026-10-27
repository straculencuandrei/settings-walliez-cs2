# CS2 Server Settings, Control Center & Custom MVP Workshop Suite

This repository contains the complete configuration, custom CounterStrikeSharp plugins, Discord integration bots, and the unified desktop Control Center for the **Walliez CS2 Server** (`81.181.113.120:27015`).

---

## ⚡ CS2 Server Control Center (`CS2_Control_Center.bat`)

The single master control application for managing all server features via a modern, high-speed glassmorphism desktop interface:

* **📢 Tab 1: In-Game Announcements (`ServerAnnouncer`)**:
  * Real-time view, add, edit, and delete scheduled chat messages.
  * Adjust announcement interval (seconds) and rotation mode (random / sequential).
  * Live **CS2 In-Game Chat Simulator Preview** with real-time color rendering (`{Gold}`, `{LightBlue}`, `{Green}`, `{LightPurple}`, etc.).
  * 1-Click Save & Deploy directly to the VPS via SFTP + instant RCON reload.
* **🏷️ Tab 2: Server Name & Hostname**:
  * Live A2S engine query of the active server name, map, and player counts.
  * Instant RCON hostname update + permanent update to `server.cfg`.
  * Live Steam & CS2 server browser card preview.
* **⚙️ Tab 3: Match Settings & Convars**:
  * Searchable and customizable competitive match rules (`mp_roundtime_defuse`, `mp_maxrounds`, `mp_freezetime`, `mp_c4timer`, `mp_buytime`, `mp_startmoney`, etc.).
  * Live RCON execution + permanent sync to `gamemode_competitive_server.cfg`.
* **🎵 Tab 4: MVP Anthem Studio & Audio Pipeline**:
  * Launch Visual MVP Web Studio (`add_mvp_ui.py`) with audio trimming & waveform preview.
  * 1-Click Local Client Sync (`sync_client_anthems.py`) to your local Steam CS2 library.
  * Audio Converter: Convert any audio to clean 44.1 kHz, 320 kbps CBR MP3.
  * Rebuild & Deploy Workshop Addon (`prepare_workshop_mvp.py`) to server cache.
  * Launch Valve CS2 Workshop Tools (`wlzMVP`).
* **📊 Tab 5: Services & Discord Bot Monitor**:
  * Live status of `cs2.service` and `cs2-discord-bot.service`.
  * Safe 1-click server restart and Discord bot restart.
  * Hot reload all CSS plugins.
  * Quick links to `skinz.walliez.xyz`, `mvpz.walliez.xyz`, and 1-click connect.

---

## 🛠️ CLI Utilities

* **`edit_announcements.py`**: Standalone interactive terminal tool to edit announcement messages, intervals, prefixes, and deploy live.
* **`set_server_name.py`**: Command-line tool to query and set hostname via RCON.
* **`cs2_cfg.py`**: Command-line interactive match convar editor.
* **`export_clean_mp3.py`**: High-performance audio conversion matching onlineaudioconverter.com algorithm.
* **`SERVER_DOCUMENTATION.md`**: Complete documentation covering server architecture, Discord bot, plugins, and administration.

