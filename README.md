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
* **🎵 Tab 4: MVP Anthem Studio & Batch Workshop Pipeline**:
  * **Interactive Vinyl Deck & Waveform Scrubber**: Modern pitch-black luxury player with rotating vinyl disc, in-game HUD banner preview (`★ doggg is MVP of the Round!`), and interactive start-point waveform seeking.
  * **Configurable Anthem Durations (5.0s - 15.0s)**: Slider per track with dynamic 1.0s audio volume fadeout (`afade=t=out`) and live visual cut region highlight.
  * **Multi-Track Batch Queue**: Add multiple audio tracks via native file dialog (`+ Select Audio Files`) or manually, configuring metadata and cut windows simultaneously.
  * **1-Click Unified Batch Pipeline (`Convert & Deploy All to Server`)**: Processes all queued anthems in one run: trims & normalizes audio, generates KV3 definitions, compiles with Valve `resourcecompiler.exe`, updates VPS `MVP_Settings.json`, builds Valve VPK cache, and synchronizes to local CS2 client directories.
  * **Bug-Free CS2 Workshop Tools Integration**: Cleanly launches `cs2.exe -tools -addon wlzMVP` to publish compiled addons directly to Steam Workshop Item `3827657422`.
  * **Active Server Anthems Table**: View, audit durations, and manage registered server soundevents.
* **📊 Tab 5: Services & Discord Bot Monitor**:
  * Live status of `cs2.service` and `cs2-discord-bot.service`.
  * Safe 1-click server restart and Discord bot restart.
  * Hot reload all CSS plugins.
  * Quick links to `skinz.walliez.xyz`, `mvpz.walliez.xyz`, and 1-click connect.

---

## 🛠️ Architecture & Documentation

* **`SERVER_DOCUMENTATION.md`**: Complete technical documentation covering server architecture, Discord bot, CounterStrikeSharp plugins, and administration:
  * **Section 8**: Troubleshooting & Gotchas Cheat Sheet.
  * **Section 12**: Desktop Control Center Architecture & MVP Studio Post-Mortem.
  * **Section 13**: Failure Modes, Diagnostic Flowcharts & Disaster Recovery Runbook (diagnostic decision tree, Python string escaping traps, route handler fallthrough, port 5890 conflict resolution, and emergency recovery commands).
* **`cs2_control_center.py`**: Unified all-in-one desktop GUI backend serving the pitch-black luxury management portal.
* **`CS2_Control_Center.bat`**: Desktop launcher that auto-starts the Control Center and seamlessly handles daemon reconnection.

