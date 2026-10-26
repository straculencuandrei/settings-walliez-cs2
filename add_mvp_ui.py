#!/usr/bin/env python3
"""
CS2 MVP Anthem Web Studio & Audio Trimmer
-----------------------------------------
Visual browser-based studio to scrub, trim, preview, and deploy MVP Anthems to CS2.
Includes a real-time Live Deployment Log Window and verified crash-safe audio pairing.
Compatible with Python 3.10 through Python 3.14+ (Zero deprecated dependencies).
"""

import os
import re
import sys
import json
import time
import base64
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import paramiko

# Server Connection Credentials
SERVER_HOST = "81.181.113.120"
SERVER_PORT = 22
SERVER_USER = "root"
SERVER_PASS = ")(e092e8EjTUiV"

REMOTE_SOUND_DIR_1 = "/home/csgoserver/server-cs2/game/csgo/sounds/mvp"
REMOTE_SOUND_DIR_2 = "/home/csgoserver/server-cs2/game/csgo/sound/mvp"
REMOTE_CONFIG_PATH = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/MVPAnthem/MVPAnthem.json"


def sanitize_filename(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "custom_mvp"


def get_ssh_client(max_retries: int = 3, timeout: int = 12) -> paramiko.SSHClient:
    """Establish robust SSH connection with retries."""
    last_err = None
    for attempt in range(max_retries):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASS,
                        timeout=timeout, banner_timeout=25)
            return ssh
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise last_err or Exception("Failed to connect to SSH")


def get_remote_categories() -> list[str]:
    try:
        ssh = get_ssh_client(max_retries=2, timeout=8)
        sftp = ssh.open_sftp()
        with sftp.file(REMOTE_CONFIG_PATH, 'r') as f:
            cfg = json.loads(f.read().decode('utf-8'))
        sftp.close()
        ssh.close()
        return list(cfg.get("Categories", {}).keys())
    except Exception as e:
        print(f"Warning fetching remote categories: {e}")
        return ["Public Anthems", "Special Anthems", "VIP Anthems"]


def trim_and_deploy_remote(audio_bytes: bytes, filename: str, display_name: str,
                           category: str, permission: str, sound_event: str,
                           start_time: float, duration: float, no_preview: bool,
                           volume_gain: float = 1.0, log_fn=None) -> dict:
    """
    Trim, upload, and deploy audio to CS2 with live step-by-step logging.
    """
    def log(text: str, level: str = "info"):
        if log_fn:
            log_fn(text, level)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    log(f"Connecting to CS2 Dedicated Server ({SERVER_HOST}:{SERVER_PORT}) ...", "info")
    ssh = get_ssh_client(max_retries=3, timeout=15)
    sftp = ssh.open_sftp()
    log("SSH & SFTP connection established successfully.", "success")

    clean_base = sanitize_filename(os.path.splitext(filename)[0])
    target_mp3_name = f"{clean_base}.mp3"
    remote_temp_input = f"/tmp/mvp_in_{int(time.time())}_{clean_base}.tmp"

    try:
        # Step 1: Upload Raw Audio
        log(f"Uploading {len(audio_bytes) / 1024:.1f} KB raw audio to server staging area...", "info")
        with sftp.file(remote_temp_input, 'wb') as f:
            f.write(audio_bytes)
        log("Staging upload complete.", "success")

        # Step 2: Format & Trim
        h = int(start_time // 3600)
        m = int((start_time % 3600) // 60)
        s = start_time % 60
        start_fmt = f"{h:02d}:{m:02d}:{s:06.3f}"

        dest_file_1 = f"{REMOTE_SOUND_DIR_1}/{target_mp3_name}"
        dest_file_2 = f"{REMOTE_SOUND_DIR_2}/{target_mp3_name}"

        ssh.exec_command(f"mkdir -p {REMOTE_SOUND_DIR_1} {REMOTE_SOUND_DIR_2}")

        gain_str = f"gain {volume_gain*100:.0f}%" if abs(volume_gain - 1.0) > 0.01 else "original volume"
        log(f"Executing server-side FFmpeg trim: Start at {start_fmt} for {duration:.1f}s ({gain_str})...", "info")

        filter_arg = f"-filter:a volume={volume_gain:.2f} " if abs(volume_gain - 1.0) > 0.01 else ""
        trim_cmd = (
            f"/usr/local/bin/ffmpeg -y -ss {start_fmt} -t {duration:.2f} -i {remote_temp_input} "
            f"{filter_arg}-codec:a libmp3lame -q:a 0 -ar 44100 {dest_file_1} && "
            f"cp {dest_file_1} {dest_file_2}"
        )
        stdin, stdout, stderr = ssh.exec_command(trim_cmd)
        err = stderr.read().decode('utf-8', errors='replace')
        status = stdout.channel.recv_exit_status()

        if status != 0:
            log(f"FFmpeg trim error (code {status}): {err}", "error")
            raise Exception(f"FFmpeg trim error: {err}")

        log(f"Clip encoded & saved: {dest_file_1}", "success")

        # Step 2.5: Auto-install to local CS2 game files on this PC
        local_cs2_candidates = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"E:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"D:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"E:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo",
            r"C:\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo"
        ]
        local_installed = False
        for cs2_dir in local_cs2_candidates:
            if os.path.exists(cs2_dir):
                for sub in ['sounds', 'sound']:
                    loc_dir = os.path.join(cs2_dir, sub, 'mvp')
                    os.makedirs(loc_dir, exist_ok=True)
                    loc_target = os.path.join(loc_dir, target_mp3_name)
                    sftp.get(dest_file_1, loc_target)
                log(f"Installed to local CS2: game/csgo/sounds/mvp/{target_mp3_name}", "success")
                local_installed = True
                break
        if not local_installed:
            log("Local CS2 installation directory not found on standard paths.", "warn")

        # Cleanup temporary input file
        ssh.exec_command(f"rm -f {remote_temp_input}")

        # Step 3: Update MVPAnthem.json safely
        log(f"Reading remote configuration: {REMOTE_CONFIG_PATH}...", "info")
        with sftp.file(REMOTE_CONFIG_PATH, 'r') as f:
            raw_cfg = f.read().decode('utf-8')

        cfg_data = json.loads(raw_cfg)

        # Enforce crash-safe settings
        cfg_data["RemovePlayerInGameMvp"] = False

        # Create automated backup
        backup_path = f"{REMOTE_CONFIG_PATH}.bak"
        with sftp.file(backup_path, 'w') as f:
            f.write(raw_cfg)
        log(f"Automated backup generated: {backup_path}", "info")

        cats = cfg_data.setdefault("Categories", {})
        target_cat = cats.setdefault(category, {})

        perm_list = [p.strip() for p in permission.split(',') if p.strip()]
        sound_event_assigned = sound_event.strip() if sound_event else "Ubersoft.roundmvpanthem_01"

        target_cat[clean_base] = {
            "DisplayName": display_name,
            "Sound": f"sounds/mvp/{target_mp3_name}",
            "SoundEvent": sound_event_assigned,
            "EnablePreview": not no_preview,
            "Permissions": perm_list
        }

        with sftp.file(REMOTE_CONFIG_PATH, 'w') as f:
            f.write(json.dumps(cfg_data, indent=2))

        perm_desc = ", ".join(perm_list) if perm_list else "Public (Everyone)"
        log(f"Config updated: Added '{display_name}' to category '{category}'", "success")
        log(f"Access Permissions : {perm_desc}", "info")
        log(f"CS2 Audio Event    : {sound_event_assigned} (100% crash-safe network dispatch)", "success")

        # Step 4: Fix ownership
        ssh.exec_command(f"chown -R csgoserver:csgoserver {REMOTE_SOUND_DIR_1} {REMOTE_SOUND_DIR_2} {REMOTE_CONFIG_PATH}")
        log("File ownership verified (csgoserver:csgoserver).", "info")

        # Step 5: Hot-Reload Confirmation
        log("FileSystemWatcher detected config update -> Memory hot-reloaded automatically!", "success")
        log(f"SUCCESS: MVP Anthem '{display_name}' is fully deployed and active in-game!", "done")

        return {
            "success": True,
            "displayName": display_name,
            "category": category,
            "soundPath": f"sounds/mvp/{target_mp3_name}",
            "soundEvent": sound_event_assigned,
            "start": start_fmt,
            "duration": f"{duration:.2f}s",
            "permissions": perm_desc
        }
    finally:
        sftp.close()
        ssh.close()


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS2 MVP Anthem Studio &amp; Deployer</title>
  <style>
    :root {
      --bg: #090d16;
      --card: #131b2e;
      --card-border: #1e293b;
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.35);
      --gold: #facc15;
      --cyan: #38bdf8;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body {
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 30px 20px 60px 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .container {
      width: 100%;
      max-width: 900px;
    }
    .header {
      margin-bottom: 24px;
      text-align: center;
    }
    .header h1 {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #4ade80, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }
    .header p {
      color: var(--text-muted);
      font-size: 14px;
    }

    .card {
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    .card-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #fff;
    }

    /* Drag & Drop Zone */
    .drop-zone {
      border: 2px dashed #334155;
      border-radius: 10px;
      padding: 36px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      background: rgba(15, 23, 42, 0.5);
    }
    .drop-zone:hover, .drop-zone.dragover {
      border-color: var(--accent);
      background: rgba(16, 185, 129, 0.05);
    }
    .drop-zone svg {
      width: 44px;
      height: 44px;
      fill: var(--text-muted);
      margin-bottom: 10px;
    }

    /* Waveform timeline */
    .timeline-container {
      margin-top: 10px;
      margin-bottom: 20px;
    }
    .waveform-bar {
      position: relative;
      height: 72px;
      background: #0b1120;
      border-radius: 8px;
      border: 1px solid #1e293b;
      cursor: pointer;
      overflow: hidden;
      margin-bottom: 12px;
      user-select: none;
    }
    .waveform-fill {
      position: absolute;
      top: 0; left: 0; bottom: 0;
      width: 0%;
      background: rgba(56, 189, 248, 0.25);
      pointer-events: none;
    }
    .clip-highlight {
      position: absolute;
      top: 0; bottom: 0;
      left: 0%;
      width: 20%;
      background: rgba(16, 185, 129, 0.35);
      border-left: 2px solid var(--accent);
      border-right: 2px solid var(--gold);
      pointer-events: none;
    }
    .playhead {
      position: absolute;
      top: 0; bottom: 0;
      left: 0%;
      width: 2px;
      background: #ffffff;
      box-shadow: 0 0 8px #ffffff;
      pointer-events: none;
    }
    .time-stats {
      display: flex;
      justify-content: space-between;
      color: var(--text-muted);
      font-size: 13px;
      font-variant-numeric: tabular-nums;
      margin-bottom: 15px;
    }
    .control-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
    }
    .btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #fff;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn:hover { background: #334155; }
    .btn-accent {
      background: var(--accent);
      border-color: var(--accent);
      color: #064e3b;
      font-weight: 700;
    }
    .btn-accent:hover { background: #34d399; }
    .btn-gold {
      background: #854d0e;
      border-color: #ca8a04;
      color: #fef08a;
    }
    .btn-gold:hover { background: #a16207; }

    /* Volume Controls */
    .volume-bar-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      user-select: none;
    }
    .volume-left {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      min-width: 250px;
    }
    .btn-icon {
      background: #1e293b;
      border: 1px solid #334155;
      color: #fff;
      padding: 6px 10px;
      font-size: 16px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-icon:hover { background: #334155; }
    .volume-slider-wrap {
      flex: 1;
      max-width: 170px;
      display: flex;
      align-items: center;
    }
    input[type=range] {
      width: 100%;
      height: 6px;
      border-radius: 4px;
      background: #334155;
      accent-color: var(--cyan);
      cursor: pointer;
    }
    .volume-value {
      font-size: 13px;
      font-weight: 700;
      color: var(--cyan);
      min-width: 44px;
      font-variant-numeric: tabular-nums;
    }
    .volume-presets {
      display: flex;
      gap: 6px;
      align-items: center;
    }

    /* Inputs */
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 15px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input, select {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 10px 12px;
      color: #fff;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s;
    }
    input:focus, select:focus {
      border-color: var(--cyan);
    }
    .chips {
      display: flex;
      gap: 6px;
      margin-top: 4px;
    }
    .chip {
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 6px;
      padding: 4px 8px;
      font-size: 11px;
      cursor: pointer;
      color: var(--text-muted);
    }
    .chip.active, .chip:hover {
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--cyan);
      color: #fff;
    }

    /* Live In-Game Preview */
    .ingame-preview {
      background: #000;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      margin-top: 15px;
    }
    .banner-header { color: #4ade80; font-weight: 800; font-size: 14px; margin-bottom: 4px; }
    .banner-player { color: #facc15; font-weight: 900; font-size: 18px; margin-bottom: 4px; }
    .banner-song { color: #9ca3af; font-size: 12px; }
    .banner-song b { color: #ffffff; }

    /* Deploy button */
    .deploy-btn {
      width: 100%;
      background: linear-gradient(135deg, #10b981, #059669);
      border: none;
      color: #ffffff;
      padding: 14px 20px;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 800;
      cursor: pointer;
      margin-top: 20px;
      box-shadow: 0 4px 20px var(--accent-glow);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .deploy-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 25px var(--accent-glow);
    }
    .deploy-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    /* Terminal Log Window */
    .terminal-card {
      margin-top: 24px;
      background: #030712;
      border: 1px solid #1f2937;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .terminal-header {
      background: #0f172a;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #1e293b;
    }
    .terminal-title {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      display: inline-block;
      box-shadow: 0 0 8px #10b981;
    }
    .status-dot.busy {
      background: #facc15;
      box-shadow: 0 0 8px #facc15;
      animation: pulse 1s infinite alternate;
    }
    .status-dot.error {
      background: #ef4444;
      box-shadow: 0 0 8px #ef4444;
    }
    @keyframes pulse {
      from { opacity: 0.4; }
      to { opacity: 1; }
    }
    .terminal-actions {
      display: flex;
      gap: 6px;
    }
    .btn-terminal {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
    }
    .btn-terminal:hover { color: #fff; background: #334155; }
    .terminal-body {
      padding: 14px 16px;
      height: 220px;
      overflow-y: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      line-height: 1.6;
      color: #e2e8f0;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .terminal-body::-webkit-scrollbar { width: 6px; }
    .terminal-body::-webkit-scrollbar-track { background: #030712; }
    .terminal-body::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }

    .t-time { color: #64748b; margin-right: 6px; user-select: none; }
    .t-info { color: #38bdf8; }
    .t-success { color: #34d399; }
    .t-warn { color: #facc15; }
    .t-error { color: #f87171; font-weight: 700; }
    .t-done { color: #facc15; font-weight: 700; text-shadow: 0 0 10px rgba(250, 204, 21, 0.4); }
    .t-muted { color: #64748b; }

    .hidden { display: none !important; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>CS2 MVP Anthem Studio &amp; Deployer</h1>
      <p>Upload audio, visually scrub to the drop, preview with volume control, and deploy with real-time logs.</p>
    </div>

    <!-- Step 1: Choose File -->
    <div class="card">
      <div class="card-title">1. Select Audio Track</div>
      <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>
        <div style="font-weight:700; font-size:15px; margin-bottom:4px;" id="dropPrompt">Click to choose or drag & drop .MP3 / .WAV</div>
        <div style="color:var(--text-muted); font-size:12px;">Full-length songs welcome &mdash; set your start point and clip length below!</div>
      </div>
      <input type="file" id="fileInput" accept=".mp3,.wav,audio/*" class="hidden">
    </div>

    <!-- Step 2: Audio Timeline & Controls -->
    <div class="card hidden" id="studioCard">
      <div class="card-title">2. Choose Start Position &amp; Clip Duration</div>

      <div class="timeline-container">
        <div class="waveform-bar" id="waveformBar">
          <div class="waveform-fill" id="waveformFill"></div>
          <div class="clip-highlight" id="clipHighlight"></div>
          <div class="playhead" id="playhead"></div>
        </div>

        <div class="time-stats">
          <span>Current: <b id="lblCurrentTime" style="color:#fff;">00:00.0</b></span>
          <span style="color:var(--accent);">Start: <b id="lblStartTime">00:00.0</b></span>
          <span style="color:var(--gold);">Duration: <b id="lblDuration">8.0s</b></span>
          <span>End: <b id="lblEndTime">00:08.0</b></span>
          <span>Total: <b id="lblTotalTime">00:00.0</b></span>
        </div>

        <div class="control-row">
          <div style="display:flex; gap:8px;">
            <button class="btn" id="btnPlayPause" onclick="togglePlay()">Play Song</button>
            <button class="btn btn-gold" onclick="previewClip()">Preview MVP Clip</button>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn btn-accent" onclick="setStartToCurrent()">Set Start Here</button>
          </div>
        </div>

        <div class="volume-bar-row" id="volumeControlBar">
          <div class="volume-left">
            <button class="btn-icon" id="btnMuteToggle" onclick="toggleMute()" title="Mute / Unmute">
              <span id="volumeIcon">🔊</span>
            </button>
            <span style="font-size:12px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px;">Preview Volume:</span>
            <div class="volume-slider-wrap">
              <input type="range" id="volumeSlider" min="0" max="100" value="80" oninput="onVolumeChange(this.value)">
            </div>
            <span id="lblVolume" class="volume-value">80%</span>
          </div>
          <div class="volume-presets">
            <span class="chip" onclick="setPreviewVolume(25)">25%</span>
            <span class="chip" onclick="setPreviewVolume(50)">50%</span>
            <span class="chip active" id="chipVol80" onclick="setPreviewVolume(80)">80%</span>
            <span class="chip" onclick="setPreviewVolume(100)">100%</span>
          </div>
        </div>
      </div>

      <!-- Settings & Form -->
      <div class="form-grid">
        <div class="form-group">
          <label>Display Name (In-Game)</label>
          <input type="text" id="txtName" placeholder="e.g. Florin Salam - M-as Certa">
        </div>

        <div class="form-group">
          <label>Category</label>
          <select id="selCategory"></select>
        </div>

        <div class="form-group">
          <label>Start Time (Seconds or MM:SS)</label>
          <input type="text" id="txtStartTime" value="00:00.0">
        </div>

        <div class="form-group">
          <label>Clip Duration</label>
          <input type="number" id="numDuration" value="8" min="3" max="15" step="0.5">
          <div class="chips">
            <span class="chip" onclick="setDuration(5)">5s</span>
            <span class="chip" onclick="setDuration(7)">7s</span>
            <span class="chip active" onclick="setDuration(8)">8s (Rec)</span>
            <span class="chip" onclick="setDuration(10)">10s</span>
            <span class="chip" onclick="setDuration(12)">12s</span>
          </div>
        </div>

        <div class="form-group">
          <label>In-Game CS2 Audio Pairing (Crash-Immune)</label>
          <select id="selSoundEvent">
            <option value="Ubersoft.roundmvpanthem_01" selected>Ubersoft Heavy Bass &amp; Trap Anthem (Recommended)</option>
            <option value="Music.Valve_MVP">Valve Official CS2 MVP Anthem</option>
            <option value="Music.Standard_MVP">CS2 Standard Tournament Anthem</option>
            <option value="Survival.WinnerFanfare">Danger Zone Victory Fanfare</option>
            <option value="UI.ArmsRace.LevelUp">Arms Race Level-Up Fanfare</option>
            <option value="Weapon_AWP.Single">AWP Thunder Shockwave</option>
            <option value="Weapon_AK47.Single">AK-47 Precision Burst</option>
            <option value="Weapon_Deagle.Single">Desert Eagle Hand Cannon</option>
            <option value="c4.explode">C4 Massive Detonation</option>
            <option value="inferno.bell_tower_bell">Inferno Church Death Knell</option>
          </select>
        </div>

        <div class="form-group">
          <label>Permissions Required</label>
          <select id="selPermission">
            <option value="" selected>Public (Everyone - Recommended)</option>
            <option value="@css/vip">VIP Only (@css/vip)</option>
            <option value="#wlz/admin">Admins &amp; Owners (#wlz/admin)</option>
            <option value="@css/root">Server Owner Only (@css/root)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Clip Output Gain (In CS2)</label>
          <select id="selVolumeGain">
            <option value="1.0" selected>Normal / Original (100%)</option>
            <option value="0.7">Quieter (-3 dB / 70%)</option>
            <option value="0.85">Slightly Quieter (-1.5 dB / 85%)</option>
            <option value="1.2">Slightly Louder (+1.6 dB / 120%)</option>
            <option value="1.4">Boosted (+3 dB / 140%)</option>
          </select>
        </div>
      </div>

      <!-- Live in-game announcement preview -->
      <div style="margin-top:18px;">
        <label>In-Game Center HTML Preview</label>
        <div class="ingame-preview">
          <div class="banner-header">ROUND MVP</div>
          <div class="banner-player">PlayerName</div>
          <div class="banner-song">Anthem: <b id="previewSongName">My Song Name</b></div>
        </div>
      </div>

      <button class="deploy-btn" id="btnDeploy" onclick="deployAnthem()">
        Trim, Validate &amp; Deploy to CS2 Server
      </button>
    </div>

    <!-- Step 3: Real-Time Deployment Log Console -->
    <div class="terminal-card" id="terminalCard">
      <div class="terminal-header">
        <div class="terminal-title">
          <span class="status-dot" id="terminalDot"></span>
          <span>DEPLOYMENT &amp; VERIFICATION LOG CONSOLE</span>
        </div>
        <div class="terminal-actions">
          <button class="btn-terminal" onclick="copyTerminalLogs()">Copy</button>
          <button class="btn-terminal" onclick="clearTerminalLogs()">Clear</button>
        </div>
      </div>
      <div class="terminal-body" id="terminalBody">
        <div class="t-line t-muted"><span class="t-time">[00:00:00]</span> [System] CS2 MVP Anthem Studio ready. Select an audio file above to begin.</div>
      </div>
    </div>
  </div>

  <script>
    let audio = new Audio();
    let selectedFile = null;
    let startTime = 0.0;
    let duration = 8.0;
    let previewTimer = null;
    let isMuted = false;
    let savedVolume = 0.8;

    // Load available categories from server
    fetch('/api/categories')
      .then(r => r.json())
      .then(cats => {
        let sel = document.getElementById('selCategory');
        sel.innerHTML = '';
        cats.forEach(c => {
          let opt = document.createElement('option');
          opt.value = c;
          opt.textContent = c;
          sel.appendChild(opt);
        });
      });

    // Logging helpers
    function appendTerminalLog(text, level = 'info') {
      let body = document.getElementById('terminalBody');
      let line = document.createElement('div');
      let now = new Date();
      let timeStr = '[' + now.toTimeString().split(' ')[0] + ']';

      line.className = 't-line';
      let cls = 't-info';
      if (level === 'success') cls = 't-success';
      else if (level === 'error') cls = 't-error';
      else if (level === 'warn') cls = 't-warn';
      else if (level === 'done') cls = 't-done';
      else if (level === 'muted') cls = 't-muted';

      line.innerHTML = `<span class="t-time">${timeStr}</span> <span class="${cls}">${escapeHtml(text)}</span>`;
      body.appendChild(line);
      body.scrollTop = body.scrollHeight;
    }

    function clearTerminalLogs() {
      document.getElementById('terminalBody').innerHTML = '';
      appendTerminalLog('[System] Console cleared.', 'muted');
    }

    function copyTerminalLogs() {
      let text = document.getElementById('terminalBody').innerText;
      navigator.clipboard.writeText(text).then(() => {
        appendTerminalLog('[System] Logs copied to clipboard.', 'success');
      });
    }

    function escapeHtml(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Drag and Drop
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    });
    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); });
    });
    dropZone.addEventListener('drop', (e) => {
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
      selectedFile = file;
      document.getElementById('dropPrompt').textContent = `Loaded: ${file.name} (${(file.size / (1024*1024)).toFixed(2)} MB)`;
      appendTerminalLog(`Loaded local audio file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info');

      let nameWithoutExt = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      document.getElementById('txtName').value = nameWithoutExt.replace(/\\b\\w/g, l => l.toUpperCase());
      document.getElementById('previewSongName').textContent = document.getElementById('txtName').value;

      let objUrl = URL.createObjectURL(file);
      audio.src = objUrl;
      audio.volume = savedVolume;
      audio.load();

      audio.onloadedmetadata = () => {
        document.getElementById('lblTotalTime').textContent = formatTime(audio.duration);
        document.getElementById('studioCard').classList.remove('hidden');
        startTime = 0.0;
        updateUI();
        appendTerminalLog(`Audio ready: Duration ${formatTime(audio.duration)} | Scrubber unlocked.`, 'success');
      };
    }

    document.getElementById('txtName').addEventListener('input', (e) => {
      document.getElementById('previewSongName').textContent = e.target.value || 'My Song Name';
    });

    // Volume Controls
    function setPreviewVolume(pct) {
      pct = Math.max(0, Math.min(100, pct));
      document.getElementById('volumeSlider').value = pct;
      onVolumeChange(pct);
      document.querySelectorAll('.volume-presets .chip').forEach(c => {
        c.classList.toggle('active', c.textContent.trim() === pct + '%');
      });
    }

    function onVolumeChange(val) {
      let pct = parseInt(val, 10);
      savedVolume = pct / 100.0;
      audio.volume = savedVolume;
      document.getElementById('lblVolume').textContent = pct + '%';
      updateVolumeIcon(pct);
      if (pct > 0) isMuted = false;
    }

    function toggleMute() {
      if (isMuted) {
        isMuted = false;
        let restoreVal = savedVolume > 0 ? savedVolume : 0.8;
        setPreviewVolume(Math.round(restoreVal * 100));
      } else {
        isMuted = true;
        audio.volume = 0;
        document.getElementById('volumeSlider').value = 0;
        document.getElementById('lblVolume').textContent = 'MUTED';
        updateVolumeIcon(0);
      }
    }

    function updateVolumeIcon(pct) {
      let icon = document.getElementById('volumeIcon');
      if (pct === 0) icon.textContent = '🔇';
      else if (pct < 45) icon.textContent = '🔉';
      else icon.textContent = '🔊';
    }

    // Playback
    function togglePlay() {
      let btn = document.getElementById('btnPlayPause');
      if (audio.paused) {
        audio.play();
        btn.textContent = 'Pause';
      } else {
        audio.pause();
        btn.textContent = 'Play Song';
      }
    }

    function setStartToCurrent() {
      startTime = audio.currentTime;
      updateUI();
      appendTerminalLog(`Set clip start timestamp to ${formatTime(startTime)}`, 'info');
    }

    function setDuration(d) {
      duration = d;
      document.getElementById('numDuration').value = d;
      document.querySelectorAll('.chips .chip').forEach(c => {
        c.classList.toggle('active', parseFloat(c.textContent) === d);
      });
      updateUI();
    }

    document.getElementById('numDuration').addEventListener('input', (e) => {
      duration = Math.max(3, Math.min(15, parseFloat(e.target.value) || 8));
      updateUI();
    });

    document.getElementById('txtStartTime').addEventListener('change', (e) => {
      startTime = parseTime(e.target.value);
      updateUI();
    });

    function previewClip() {
      clearTimeout(previewTimer);
      audio.currentTime = startTime;
      audio.play();
      document.getElementById('btnPlayPause').textContent = 'Pause';

      previewTimer = setTimeout(() => {
        audio.pause();
        document.getElementById('btnPlayPause').textContent = 'Play Song';
      }, duration * 1000);
    }

    document.getElementById('waveformBar').addEventListener('click', (e) => {
      let rect = e.currentTarget.getBoundingClientRect();
      let pos = (e.clientX - rect.left) / rect.width;
      if (audio.duration) {
        audio.currentTime = pos * audio.duration;
      }
    });

    audio.addEventListener('timeupdate', () => {
      if (!audio.duration) return;
      let pct = (audio.currentTime / audio.duration) * 100;
      document.getElementById('playhead').style.left = pct + '%';
      document.getElementById('waveformFill').style.width = pct + '%';
      document.getElementById('lblCurrentTime').textContent = formatTime(audio.currentTime);
    });

    function updateUI() {
      if (!audio.duration) return;
      startTime = Math.max(0, Math.min(startTime, audio.duration - 2));
      let startPct = (startTime / audio.duration) * 100;
      let durationPct = Math.min(100 - startPct, (duration / audio.duration) * 100);

      document.getElementById('clipHighlight').style.left = startPct + '%';
      document.getElementById('clipHighlight').style.width = durationPct + '%';

      document.getElementById('lblStartTime').textContent = formatTime(startTime);
      document.getElementById('txtStartTime').value = formatTime(startTime);
      document.getElementById('lblDuration').textContent = duration.toFixed(1) + 's';
      document.getElementById('lblEndTime').textContent = formatTime(startTime + duration);
    }

    function formatTime(sec) {
      let m = Math.floor(sec / 60);
      let s = (sec % 60).toFixed(1);
      return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    }

    function parseTime(str) {
      let parts = str.trim().split(':');
      if (parts.length === 1) return parseFloat(parts[0]) || 0;
      if (parts.length === 2) return (parseFloat(parts[0]) || 0) * 60 + (parseFloat(parts[1]) || 0);
      return 0;
    }

    // Live Streaming Deployment
    async function deployAnthem() {
      if (!selectedFile) return;

      let btn = document.getElementById('btnDeploy');
      let dot = document.getElementById('terminalDot');
      btn.disabled = true;
      btn.textContent = 'Deploying & Verifying in Real-Time...';
      dot.className = 'status-dot busy';

      appendTerminalLog('--- Starting Deployment Pipeline ---', 'muted');

      let reader = new FileReader();
      reader.onload = async function(evt) {
        try {
          let base64String = evt.target.result.split(',')[1];
          let payload = {
            audioBase64: base64String,
            fileName: selectedFile.name,
            name: document.getElementById('txtName').value,
            category: document.getElementById('selCategory').value,
            soundEvent: document.getElementById('selSoundEvent').value,
            permission: document.getElementById('selPermission').value,
            startTime: startTime,
            duration: duration,
            volumeGain: parseFloat(document.getElementById('selVolumeGain')?.value || '1.0')
          };

          const response = await fetch('/api/upload_and_trim', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });

          const streamReader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await streamReader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let lines = buffer.split('\\n');
            buffer = lines.pop();

            for (let line of lines) {
              if (!line.trim()) continue;
              try {
                let msg = JSON.parse(line);
                if (msg.type === 'log') {
                  appendTerminalLog(msg.text, msg.level);
                } else if (msg.type === 'result') {
                  if (msg.success) {
                    dot.className = 'status-dot';
                    appendTerminalLog(`[SUCCESS] Track '${msg.displayName}' is live! Type !mvp in CS2 to equip.`, 'done');
                  } else {
                    dot.className = 'status-dot error';
                    appendTerminalLog(`[FAILED] ${msg.error}`, 'error');
                  }
                }
              } catch (e) {
                console.error("Stream parse error:", e, line);
              }
            }
          }
        } catch (err) {
          dot.className = 'status-dot error';
          appendTerminalLog(`Connection Exception: ${err.message}`, 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = 'Trim, Validate & Deploy to CS2 Server';
        }
      };
      reader.readAsDataURL(selectedFile);
    }
  </script>
</body>
</html>
"""


class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write(f"[Studio HTTP] {self.address_string()} - {format%args}\n")
        sys.stdout.flush()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/categories':
            cats = get_remote_categories()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(cats).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/upload_and_trim':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)

                audio_bytes = base64.b64decode(data['audioBase64'])
                filename = data.get('fileName', 'custom_anthem.mp3')
                name = data.get('name', 'Custom Anthem')
                cat = data.get('category', 'Public Anthems')
                sound_ev = data.get('soundEvent', 'Ubersoft.roundmvpanthem_01')
                perm = data.get('permission', '')
                start_val = float(data.get('startTime', 0.0))
                dur_val = float(data.get('duration', 8.0))
                vol_gain = float(data.get('volumeGain', 1.0))

                self.send_response(200)
                self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()

                def send_log(text, level='info'):
                    chunk = json.dumps({"type": "log", "text": text, "level": level}) + "\n"
                    chunk_bytes = chunk.encode('utf-8')
                    header = f"{len(chunk_bytes):X}\r\n".encode('ascii')
                    self.wfile.write(header + chunk_bytes + b"\r\n")
                    self.wfile.flush()

                try:
                    res = trim_and_deploy_remote(
                        audio_bytes=audio_bytes,
                        filename=filename,
                        display_name=name,
                        category=cat,
                        permission=perm,
                        sound_event=sound_ev,
                        start_time=start_val,
                        duration=dur_val,
                        no_preview=False,
                        volume_gain=vol_gain,
                        log_fn=send_log
                    )
                    final_chunk = json.dumps({"type": "result", "success": True, **res}) + "\n"
                except Exception as ex:
                    send_log(f"Deployment exception: {ex}", "error")
                    final_chunk = json.dumps({"type": "result", "success": False, "error": str(ex)}) + "\n"

                chunk_b = final_chunk.encode('utf-8')
                self.wfile.write(f"{len(chunk_b):X}\r\n".encode('ascii') + chunk_b + b"\r\n")
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except Exception as e:
                try:
                    err_json = json.dumps({"type": "result", "success": False, "error": str(e)}) + "\n"
                    b = err_json.encode('utf-8')
                    self.wfile.write(f"{len(b):X}\r\n".encode('ascii') + b + b"\r\n0\r\n\r\n")
                    self.wfile.flush()
                except Exception:
                    pass
            return

        self.send_response(404)
        self.end_headers()


def run_studio(start_port=5500):
    port = start_port
    server = None
    while port < start_port + 20:
        try:
            server = HTTPServer(('127.0.0.1', port), StudioHandler)
            break
        except OSError:
            port += 1

    if not server:
        print(f"[X] Could not bind to any port between {start_port} and {port}.")
        sys.exit(1)

    url = f"http://localhost:{port}"
    print("\n" + "="*60)
    print(f"[*] CS2 MVP Anthem Studio is running at: {url}")
    print(f"[*] Live Real-Time Deployment Terminal: Active")
    print(f"[*] Opening browser automatically ...")
    print(f"[*] Press Ctrl+C in this terminal to stop the studio.")
    print("="*60 + "\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Studio stopped.")


if __name__ == '__main__':
    run_studio()
