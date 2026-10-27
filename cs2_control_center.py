#!/usr/bin/env python3
"""
CS2 Unified Server Control Center
=================================
Modern, ultra-fast web-based desktop application for managing all CS2 server
features, announcements, convars, server title, Discord bot, and MVP anthems.
"""

import os
import re
import sys
import json
import time
import socket
import struct
import shutil
import base64
import urllib.request
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import paramiko

# Configuration
SERVER_HOST = "81.181.113.120"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = ")(e092e8EjTUiV"
RCON_PORT = 27015
RCON_PASS = "walliez_rcon_2026"

REMOTE_ANNOUNCER_PATH = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/ServerAnnouncer/ServerAnnouncer.json"
REMOTE_SERVER_CFG = "/home/csgoserver/server-cs2/game/csgo/cfg/server.cfg"
REMOTE_COMP_CFG = "/home/csgoserver/server-cs2/game/csgo/cfg/gamemode_competitive_server.cfg"

FFMPEG_CANDIDATES = [
    r"C:\Users\buzunar\Documents\game\ytallinone\bin\ffmpeg.exe",
    shutil.which("ffmpeg") or ""
]

def find_ffmpeg():
    for p in FFMPEG_CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None

def get_ssh_client(timeout=8):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASS, timeout=timeout)
    return ssh

def rcon_exec(command, timeout=3.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((SERVER_HOST, RCON_PORT))
        auth = struct.pack('<iii', len(RCON_PASS) + 10, 1, 3) + RCON_PASS.encode('ascii') + b'\x00\x00'
        s.send(auth)
        s.recv(4096)
        exec_pkt = struct.pack('<iii', len(command) + 10, 2, 2) + command.encode('ascii') + b'\x00\x00'
        s.send(exec_pkt)
        out = s.recv(4096)
        s.close()
        return out[12:].decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"RCON Error: {e}"

def a2s_info():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        query = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(query, (SERVER_HOST, RCON_PORT))
        resp, _ = sock.recvfrom(4096)
        if resp.startswith(b'\xFF\xFF\xFF\xFF\x41'):
            challenge = resp[5:9]
            sock.sendto(query + challenge, (SERVER_HOST, RCON_PORT))
            resp, _ = sock.recvfrom(4096)
        sock.close()
        if len(resp) >= 6 and resp[4:5] == b'I':
            idx = 5
            protocol = resp[idx]
            idx += 1
            end = resp.find(b'\x00', idx)
            name = resp[idx:end].decode('utf-8', errors='replace')
            idx = end + 1
            end = resp.find(b'\x00', idx)
            map_name = resp[idx:end].decode('utf-8', errors='replace')
            idx = end + 1
            end = resp.find(b'\x00', idx) # folder
            idx = end + 1
            end = resp.find(b'\x00', idx) # game
            idx = end + 1 + 2 # skip appid
            players = resp[idx]
            max_players = resp[idx+1]
            return {"online": True, "name": name, "map": map_name, "players": players, "max_players": max_players}
    except Exception:
        pass
    return {"online": False, "name": "Counter-Strike 2 Server", "map": "Unknown", "players": 0, "max_players": 24}

# HTML Template with Pitch-Black Minimalist Luxury UI (Zero Emojis)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS2 Server Control Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #000000;
      --card-bg: #080808;
      --card-border: #1a1a1a;
      --card-border-subtle: #121212;
      --primary: #ffffff;
      --primary-hover: #e4e4e7;
      --accent: #27272a;
      --success: #22c55e;
      --warning: #eab308;
      --danger: #ef4444;
      --text: #ededed;
      --text-muted: #71717a;
      --text-dim: #52525b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    /* Header */
    header {
      background: #000000;
      border-bottom: 1px solid var(--card-border);
      padding: 0 24px;
      height: 54px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 28px;
      height: 28px;
      background: #111111;
      border: 1px solid #27272a;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: #ffffff;
    }
    .brand-title {
      font-size: 0.92rem;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: #ffffff;
    }
    .brand-sub {
      font-size: 0.7rem;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }
    .status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #09090b;
      border: 1px solid var(--card-border);
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 500;
      color: #a1a1aa;
      font-family: 'JetBrains Mono', monospace;
    }
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px rgba(34, 197, 94, 0.7);
    }

    /* App Container & Navigation */
    .app-container {
      max-width: 1100px;
      margin: 0 auto;
      width: 100%;
      padding: 20px 24px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .nav-tabs {
      display: flex;
      gap: 4px;
      background: #080808;
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 500;
      letter-spacing: 0.02em;
      padding: 0 14px;
      height: 32px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text);
      background: #111111;
    }
    .tab-btn.active {
      color: #ffffff;
      background: #141414;
      border-color: #27272a;
      font-weight: 600;
    }

    /* Tab Content Cards */
    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.2s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(2px); } to { opacity: 1; transform: translateY(0); } }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 14px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--card-border-subtle);
      flex-wrap: wrap;
    }
    .card-title {
      font-size: 0.92rem;
      font-weight: 600;
      color: #ffffff;
      letter-spacing: -0.01em;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .card-desc {
      font-size: 0.76rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Form Fields */
    .form-group {
      margin-bottom: 14px;
    }
    label {
      display: block;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }
    input[type="text"], input[type="number"], select {
      width: 100%;
      background: #030303;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 0 12px;
      height: 34px;
      color: #f4f4f5;
      font-family: inherit;
      font-size: 0.82rem;
      outline: none;
      transition: border-color 0.15s;
    }
    input[type="text"]:focus, input[type="number"]:focus, select:focus {
      border-color: #3f3f46;
    }
    .input-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-bottom: 14px;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: #ffffff;
      color: #000000;
      border: 1px solid #ffffff;
      border-radius: 5px;
      padding: 0 14px;
      height: 32px;
      font-weight: 600;
      font-size: 0.78rem;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
      flex-shrink: 0;
      text-decoration: none;
    }
    .btn:hover {
      background: #e4e4e7;
      border-color: #e4e4e7;
    }
    .btn-secondary {
      background: #111111;
      color: #d4d4d8;
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover {
      background: #18181b;
      color: #ffffff;
      border-color: #3f3f46;
    }
    .btn-danger {
      background: rgba(239, 68, 68, 0.08);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.25);
    }
    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.2);
      color: #ffffff;
      border-color: #ef4444;
    }
    .btn-sm {
      height: 26px;
      padding: 0 10px;
      font-size: 0.72rem;
      border-radius: 4px;
    }

    /* Message Item Rows */
    .msg-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 18px;
    }
    .msg-item {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .msg-text-box {
      flex: 1 1 auto;
      min-width: 0;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: #e4e4e7;
      word-break: break-word;
    }
    .msg-actions {
      flex-shrink: 0;
      display: flex;
      gap: 6px;
    }

    /* CS2 In-Game Chat Simulator */
    .cs2-chat-sim {
      background: #000000;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 14px;
      font-family: 'Segoe UI', Tahoma, sans-serif;
      font-size: 0.88rem;
      min-height: 48px;
      display: flex;
      align-items: center;
      margin-top: 8px;
    }
    .cs2-chat-label {
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-top: 14px;
      margin-bottom: 4px;
    }
    .cs2-preview-text {
      color: #ffffff;
      line-height: 1.4;
      font-weight: 500;
    }

    /* Color Palette Pills */
    .color-tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .color-tag-pill {
      font-size: 0.7rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 0 7px;
      height: 22px;
      line-height: 20px;
      border-radius: 4px;
      background: #0d0d0d;
      cursor: pointer;
      border: 1px solid var(--card-border);
      transition: background 0.15s, border-color 0.15s;
    }
    .color-tag-pill:hover {
      background: #18181b;
      border-color: #3f3f46;
    }

    /* Convars Dense Settings Grid */
    .convars-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 8px;
    }
    .convar-row {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .convar-meta {
      flex: 1 1 auto;
      min-width: 0;
    }
    .convar-name {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 600;
      color: #ffffff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .convar-desc {
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .convar-input {
      width: 76px !important;
      height: 28px !important;
      padding: 0 8px !important;
      font-family: 'JetBrains Mono', monospace !important;
      font-size: 0.78rem !important;
      text-align: right;
      flex-shrink: 0;
      background: #000000 !important;
      border: 1px solid var(--card-border) !important;
      border-radius: 4px !important;
      color: #ffffff !important;
    }

    /* Action Rows for MVP Studio & FastDL */
    .action-rows-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .action-row {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .action-row-meta {
      flex: 1 1 280px;
    }
    .action-row-title {
      font-size: 0.84rem;
      font-weight: 600;
      color: #ffffff;
    }
    .action-row-desc {
      font-size: 0.74rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Services Grid */
    .services-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .service-card {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 12px;
    }
    .service-card .btn {
      width: 100%;
      height: 30px;
    }

    /* Summary Stat Cards */
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .summary-card {
      background: #040404;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 12px 14px;
    }
    .summary-label {
      font-size: 0.7rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }
    .summary-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      font-weight: 600;
      color: #ffffff;
      margin-top: 4px;
      word-break: break-all;
    }

    /* Terminal Output Drawer */
    .terminal-drawer {
      background: #000000;
      border: 1px solid #18181b;
      border-radius: 4px;
      padding: 10px 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.74rem;
      line-height: 1.5;
      max-height: 120px;
      overflow-y: auto;
      color: #a1a1aa;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">CS2</div>
      <div>
        <div class="brand-title">Server Control Center</div>
        <div class="brand-sub">81.181.113.120:27015 | talent.walliez.xyz</div>
      </div>
    </div>
    <div class="status-badge" id="headerStatusBadge">
      <span class="status-dot"></span>
      <span id="headerStatusText">Checking Server...</span>
    </div>
  </header>

  <div class="app-container">

    <!-- Navigation Tabs -->
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('tab-announcements')">Announcements</button>
      <button class="tab-btn" onclick="switchTab('tab-hostname')">Server Name</button>
      <button class="tab-btn" onclick="switchTab('tab-convars')">Match Convars</button>
      <button class="tab-btn" onclick="switchTab('tab-mvp')">MVP Anthems</button>
      <button class="tab-btn" onclick="switchTab('tab-services')">Services & Bot</button>
    </div>

    <!-- TAB 1: Announcements Manager -->
    <div id="tab-announcements" class="tab-content active">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">ServerAnnouncer Settings</div>
            <div class="card-desc">Scheduled in-game chat messages promoting skinz, mvpz, and community links.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadAnnouncements()">Reload Config</button>
        </div>

        <div class="input-row">
          <div class="form-group">
            <label>Interval (Seconds)</label>
            <input type="number" id="announcerInterval" min="15" max="600" value="90">
          </div>
          <div class="form-group">
            <label>Rotation Mode</label>
            <select id="announcerRandom">
              <option value="true">Random Order (Non-Repeating)</option>
              <option value="false">Sequential Order (List Sequence)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Announcement Prefix</label>
          <input type="text" id="announcerPrefix" value="{Gold}[Walliez]{Default}" oninput="updateChatPreview()">
          <div class="color-tags-container">
            <span class="color-tag-pill" onclick="insertColorTag('{Gold}')" style="color: #E4AE39;">{Gold}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightBlue}')" style="color: #5E98D9;">{LightBlue}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Green}')" style="color: #40FF40;">{Green}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightPurple}')" style="color: #D32CE6;">{LightPurple}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{LightYellow}')" style="color: #E5E24D;">{LightYellow}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Red}')" style="color: #FF4040;">{Red}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Default}')" style="color: #FFFFFF;">{Default}</span>
            <span class="color-tag-pill" onclick="insertColorTag('{Grey}')" style="color: #CCCCCC;">{Grey}</span>
          </div>
        </div>

        <div class="card-header" style="margin-top: 18px; margin-bottom: 10px;">
          <div class="card-title" style="font-size: 0.84rem;">Active Announcement Messages</div>
          <button class="btn btn-sm" onclick="addNewMessagePrompt()">Add Message</button>
        </div>

        <div class="msg-list" id="announcementsList">
          <div style="color: var(--text-muted); font-size: 0.8rem;">Loading messages...</div>
        </div>

        <div class="cs2-chat-label">Live In-Game Chat Simulator Preview:</div>
        <div class="cs2-chat-sim">
          <div class="cs2-preview-text" id="cs2ChatSimPreview">Previewing announcement...</div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end; gap: 8px;">
          <button class="btn btn-secondary" onclick="loadAnnouncements()">Cancel</button>
          <button class="btn" onclick="saveAnnouncementsToServer()">Save & Deploy Live</button>
        </div>
      </div>
    </div>

    <!-- TAB 2: Server Hostname & Title -->
    <div id="tab-hostname" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Server Hostname & Title</div>
            <div class="card-desc">Instantly updates the live CS2 server name via RCON and saves permanently to server.cfg.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadHostname()">Query Live Name</button>
        </div>

        <div class="form-group">
          <label>Server Hostname</label>
          <input type="text" id="serverHostnameInput" placeholder="Counter-Strike 2 Server" oninput="updateHostnamePreview()">
        </div>

        <div class="cs2-chat-label" style="margin-top: 14px;">Steam & CS2 Server Browser Preview:</div>
        <div style="background: #040404; border: 1px solid var(--card-border); border-radius: 6px; padding: 14px; margin-top: 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;">
            <div style="font-weight: 600; font-size: 0.95rem; color: #ffffff;" id="hostnamePreviewText">talent.walliez.xyz</div>
            <div style="font-size: 0.76rem; color: #22c55e; font-family: 'JetBrains Mono', monospace;">Online | 81.181.113.120:27015</div>
          </div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveHostname()">Apply Hostname</button>
        </div>
      </div>
    </div>

    <!-- TAB 3: Match Settings & Convars -->
    <div id="tab-convars" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Match Settings & Convar Editor</div>
            <div class="card-desc">Tune round timers, overtime, economy, and competitive match rules.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadConvars()">Fetch Convars</button>
        </div>

        <div class="form-group">
          <input type="text" id="convarSearch" placeholder="Search convars by name or description..." oninput="filterConvars()">
        </div>

        <div class="convars-grid" id="convarsGrid">
          <!-- Populated by JS -->
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveConvars()">Apply Convar Settings</button>
        </div>
      </div>
    </div>

    <!-- TAB 4: MVP Anthems & FastDL -->
    <div id="tab-mvp" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">MVP Anthem Studio & FastDL</div>
            <div class="card-desc">Convert, sync, and deploy custom music pack anthems to CS2 and local game files.</div>
          </div>
        </div>

        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-label">Workshop Addon</div>
            <div class="summary-val" style="color: #ffffff;">wlzMVP (3827657422)</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">FastDL URL</div>
            <div class="summary-val" style="color: #ffffff;">http://81.181.113.120/fastdl/</div>
          </div>
        </div>

        <div class="action-rows-list">
          <div class="action-row">
            <div class="action-row-meta">
              <div class="action-row-title">Visual MVP Web Studio</div>
              <div class="action-row-desc">Interactive browser waveform scrubber, player preview, trim controls, and live deployment.</div>
            </div>
            <button class="btn" onclick="launchVisualStudio()">Open Visual Studio</button>
          </div>

          <div class="action-row">
            <div class="action-row-meta">
              <div class="action-row-title">1-Click Local Client Sync</div>
              <div class="action-row-desc">Sync all server MVP Anthems directly to your local Counter-Strike 2 Steam directory.</div>
            </div>
            <button class="btn btn-secondary" onclick="triggerClientSync()">Sync Local CS2</button>
          </div>

          <div class="action-row">
            <div class="action-row-meta">
              <div class="action-row-title">Clean 44.1kHz MP3 Audio Converter</div>
              <div class="action-row-desc">Converts audio using exact 320kbps 44.1kHz CBR algorithm with stripped ID3 metadata.</div>
            </div>
            <button class="btn btn-secondary" onclick="openFileConverterPrompt()">Convert Audio File</button>
          </div>

          <div class="action-row">
            <div class="action-row-meta">
              <div class="action-row-title">Rebuild & Deploy Workshop Addon (wlzMVP)</div>
              <div class="action-row-desc">Compiles all staged tracks to vsnd_c, generates VPK, and uploads to server workshop cache.</div>
            </div>
            <button class="btn btn-secondary" onclick="triggerWorkshopRebuild()">Rebuild Workshop Addon</button>
          </div>

          <div class="action-row">
            <div class="action-row-meta">
              <div class="action-row-title">Counter-Strike 2 Workshop Tools</div>
              <div class="action-row-desc">Launches the official Counter-Strike 2 Workshop Tools editor with wlzMVP loaded.</div>
            </div>
            <button class="btn btn-secondary" onclick="launchWorkshopTools()">Launch CS2 Tools</button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 5: Services & Discord Bot -->
    <div id="tab-services" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">VPS Services & Discord Bot</div>
            <div class="card-desc">Control server services, restart processes, and verify connectivity.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="refreshServices()">Refresh Status</button>
        </div>

        <div class="services-grid">
          <div class="service-card">
            <div>
              <div class="summary-label">CS2 Game Server</div>
              <div class="summary-val" id="statCs2Status" style="color: #22c55e;">Active (Running)</div>
            </div>
            <button class="btn btn-danger" onclick="serviceAction('restart_cs2')">Restart CS2 Server</button>
          </div>
          <div class="service-card">
            <div>
              <div class="summary-label">Discord 24/7 Bot</div>
              <div class="summary-val" id="statBotStatus" style="color: #22c55e;">Active (Running)</div>
            </div>
            <button class="btn btn-secondary" onclick="serviceAction('restart_bot')">Restart Discord Bot</button>
          </div>
          <div class="service-card">
            <div>
              <div class="summary-label">CSS Plugins Core</div>
              <div class="summary-val" style="color: #ffffff;">Loaded</div>
            </div>
            <button class="btn btn-secondary" onclick="serviceAction('reload_plugins')">Reload All Plugins</button>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <label style="margin-bottom: 8px;">Direct Panel Links</label>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <a href="https://skinz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm">Skin & Knife Panel</a>
            <a href="https://mvpz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm">MVP Anthems Panel</a>
            <a href="https://skinz.walliez.xyz/connect/" target="_blank" class="btn btn-secondary btn-sm">Steam Connect Page</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Log Terminal Drawer -->
    <div class="card" style="padding: 14px; margin-bottom: 0;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Activity Log</div>
        <button class="btn btn-sm btn-secondary" style="height: 22px; padding: 0 8px; font-size: 0.68rem;" onclick="clearLogs()">Clear</button>
      </div>
      <div class="terminal-drawer" id="terminalLog">Control Center ready. Connected to 81.181.113.120.</div>
    </div>

  </div>

  <script>
    function log(text) {
      const term = document.getElementById('terminalLog');
      const time = new Date().toLocaleTimeString();
      term.innerHTML += `\\n[${time}] ${text}`;
      term.scrollTop = term.scrollHeight;
    }
    function clearLogs() {
      document.getElementById('terminalLog').innerHTML = 'Log cleared.';
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.target.classList.add('active');
      if (tabId === 'tab-announcements') loadAnnouncements();
      if (tabId === 'tab-hostname') loadHostname();
      if (tabId === 'tab-convars') loadConvars();
      if (tabId === 'tab-services') refreshServices();
    }

    // CS2 Color Parser
    const CS2_COLORS = {
      '{Gold}': '#E4AE39',
      '{LightBlue}': '#5E98D9',
      '{Green}': '#40FF40',
      '{LightPurple}': '#D32CE6',
      '{LightYellow}': '#E5E24D',
      '{Red}': '#FF4040',
      '{Default}': '#FFFFFF',
      '{White}': '#FFFFFF',
      '{Grey}': '#CCCCCC',
      '{Lime}': '#40FF40',
      '{Blue}': '#5E98D9',
      '{Purple}': '#D32CE6'
    };

    function parseCs2Colors(text) {
      let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      for (const [tag, hex] of Object.entries(CS2_COLORS)) {
        html = html.split(tag).join(`</span><span style="color:${hex};">`);
      }
      return `<span>${html}</span>`;
    }

    // Announcements state
    let announcementsData = {
      IntervalSeconds: 90,
      RandomOrder: true,
      Prefix: "{Gold}[Walliez]{Default}",
      Messages: []
    };

    async function loadAnnouncements() {
      log('Fetching announcements configuration from VPS...');
      try {
        const res = await fetch('/api/announcements');
        announcementsData = await res.json();
        document.getElementById('announcerInterval').value = announcementsData.IntervalSeconds || 90;
        document.getElementById('announcerRandom').value = announcementsData.RandomOrder ? "true" : "false";
        document.getElementById('announcerPrefix').value = announcementsData.Prefix || "{Gold}[Walliez]{Default}";
        renderAnnouncementsList();
        log('Announcements loaded successfully.');
      } catch (e) {
        log('[ERROR] Error loading announcements: ' + e);
      }
    }

    function renderAnnouncementsList() {
      const container = document.getElementById('announcementsList');
      container.innerHTML = '';
      if (!announcementsData.Messages || announcementsData.Messages.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem;">No messages currently configured.</div>';
        updateChatPreview();
        return;
      }
      announcementsData.Messages.forEach((msg, idx) => {
        const item = document.createElement('div');
        item.className = 'msg-item';
        item.innerHTML = `
          <div class="msg-text-box">
            <span style="color:#71717a; font-weight:700; margin-right:8px;">#${idx+1}</span>
            <span>${msg}</span>
          </div>
          <div class="msg-actions">
            <button class="btn btn-sm btn-secondary" onclick="editMessagePrompt(${idx})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="deleteMessage(${idx})">Delete</button>
          </div>
        `;
        container.appendChild(item);
      });
      updateChatPreview();
    }

    function updateChatPreview() {
      const prefix = document.getElementById('announcerPrefix').value || '';
      const firstMsg = announcementsData.Messages && announcementsData.Messages.length > 0 ? announcementsData.Messages[0] : 'No announcement message selected.';
      const fullText = (prefix ? prefix + ' ' : '') + firstMsg;
      document.getElementById('cs2ChatSimPreview').innerHTML = parseCs2Colors(fullText);
    }

    function insertColorTag(tag) {
      const prefixInput = document.getElementById('announcerPrefix');
      prefixInput.value += tag;
      updateChatPreview();
    }

    function addNewMessagePrompt() {
      const text = prompt("Enter new announcement message:\\n\\nUse tags like: {Gold}, {LightBlue}, {Green}, {LightPurple}, {Default}");
      if (text && text.trim()) {
        announcementsData.Messages.push(text.trim());
        renderAnnouncementsList();
      }
    }

    function editMessagePrompt(idx) {
      const current = announcementsData.Messages[idx];
      const updated = prompt("Edit announcement message:", current);
      if (updated !== null && updated.trim()) {
        announcementsData.Messages[idx] = updated.trim();
        renderAnnouncementsList();
      }
    }

    function deleteMessage(idx) {
      if (confirm("Delete this announcement message?")) {
        announcementsData.Messages.splice(idx, 1);
        renderAnnouncementsList();
      }
    }

    async function saveAnnouncementsToServer() {
      log('Saving announcements to server and hot-reloading plugin...');
      announcementsData.IntervalSeconds = parseInt(document.getElementById('announcerInterval').value) || 90;
      announcementsData.RandomOrder = document.getElementById('announcerRandom').value === "true";
      announcementsData.Prefix = document.getElementById('announcerPrefix').value;

      try {
        const res = await fetch('/api/announcements', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(announcementsData)
        });
        const out = await res.json();
        if (out.success) {
          log('[OK] Announcements saved and ServerAnnouncer hot-reloaded via RCON.');
          alert('Announcements successfully deployed to the server.');
        } else {
          log('[ERROR] Error saving announcements: ' + out.error);
        }
      } catch (e) {
        log('[ERROR] Request failed: ' + e);
      }
    }

    // Hostname Management
    async function loadHostname() {
      log('Querying current hostname from server...');
      try {
        const res = await fetch('/api/hostname');
        const data = await res.json();
        document.getElementById('serverHostnameInput').value = data.hostname || '';
        updateHostnamePreview();
        log(`Server Hostname: "${data.hostname}"`);
      } catch (e) {
        log('[ERROR] Error querying hostname: ' + e);
      }
    }

    function updateHostnamePreview() {
      const name = document.getElementById('serverHostnameInput').value || 'Counter-Strike 2 Server';
      document.getElementById('hostnamePreviewText').innerText = name;
    }

    async function saveHostname() {
      const name = document.getElementById('serverHostnameInput').value;
      if (!name) return alert('Hostname cannot be empty');
      log(`Applying hostname: "${name}"...`);
      try {
        const res = await fetch('/api/hostname', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({hostname: name})
        });
        const out = await res.json();
        if (out.success) {
          log('[OK] Hostname updated immediately in live server & server.cfg.');
          alert('Hostname applied successfully.');
        } else {
          log('[ERROR] Error: ' + out.error);
        }
      } catch (e) {
        log('[ERROR] Request failed: ' + e);
      }
    }

    // Convars
    let currentConvars = [];
    async function loadConvars() {
      log('Loading server convars...');
      try {
        const res = await fetch('/api/convars');
        currentConvars = await res.json();
        renderConvars(currentConvars);
        log(`Loaded ${currentConvars.length} convars.`);
      } catch (e) {
        log('[ERROR] Error loading convars: ' + e);
      }
    }

    function renderConvars(convars) {
      const grid = document.getElementById('convarsGrid');
      grid.innerHTML = '';
      convars.forEach(item => {
        const row = document.createElement('div');
        row.className = 'convar-row';
        row.innerHTML = `
          <div class="convar-meta">
            <div class="convar-name">${item.name}</div>
            <div class="convar-desc">${item.desc}</div>
          </div>
          <input type="text" class="convar-input" id="cv_${item.name}" value="${item.value}">
        `;
        grid.appendChild(row);
      });
    }

    function filterConvars() {
      const q = document.getElementById('convarSearch').value.toLowerCase();
      const filtered = currentConvars.filter(c => c.name.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q));
      renderConvars(filtered);
    }

    async function saveConvars() {
      log('Applying convar changes via RCON and updating config files...');
      const updates = {};
      currentConvars.forEach(c => {
        const input = document.getElementById(`cv_${c.name}`);
        if (input) updates[c.name] = input.value;
      });
      try {
        const res = await fetch('/api/convars', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(updates)
        });
        const out = await res.json();
        log('[OK] Convars applied successfully via RCON.');
        alert('Convar settings updated live on the server.');
      } catch (e) {
        log('[ERROR] Error applying convars: ' + e);
      }
    }

    // Service Actions
    async function serviceAction(action) {
      if (!confirm(`Execute action: ${action}?`)) return;
      log(`Triggering action: ${action}...`);
      try {
        const res = await fetch('/api/service/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: action})
        });
        const out = await res.json();
        log(`Result: ${out.output || out.status}`);
        refreshServices();
      } catch (e) {
        log('[ERROR] Action error: ' + e);
      }
    }

    async function refreshServices() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('headerStatusText').innerText = data.online ? `Online (${data.players}/${data.max_players})` : 'Offline';
        document.getElementById('statCs2Status').innerText = data.online ? `Active (${data.map})` : 'Stopped';
        document.getElementById('statCs2Status').style.color = data.online ? '#22c55e' : '#ef4444';
      } catch (e) {}
    }

    async function triggerClientSync() {
      log('Running client anthem sync...');
      try {
        const res = await fetch('/api/sync_client', { method: 'POST' });
        const out = await res.json();
        log(out.output || 'Sync completed.');
        alert('Local CS2 client sync finished.');
      } catch (e) {
        log('[ERROR] Sync error: ' + e);
      }
    }

    async function launchVisualStudio() {
      log('Launching Visual MVP Web Studio...');
      try {
        const res = await fetch('/api/launch_visual_studio', { method: 'POST' });
        const out = await res.json();
        log(out.message || 'Visual MVP Studio launched.');
      } catch (e) {
        log('[ERROR] Error launching studio: ' + e);
      }
    }

    async function triggerWorkshopRebuild() {
      if (!confirm('Rebuild all staged anthems, compile to vsnd_c, and deploy VPK to server?')) return;
      log('Building and compiling Workshop Addon wlzMVP... (this may take 20-40s)');
      try {
        const res = await fetch('/api/rebuild_workshop', { method: 'POST' });
        const out = await res.json();
        log(out.output || 'Rebuild complete.');
        alert('Workshop Addon rebuilt and deployed to server.');
      } catch (e) {
        log('[ERROR] Error rebuilding addon: ' + e);
      }
    }

    async function launchWorkshopTools() {
      log('Launching Counter-Strike 2 Workshop Tools for wlzMVP...');
      try {
        const res = await fetch('/api/launch_workshop_tools', { method: 'POST' });
        const out = await res.json();
        log(out.message || 'CS2 Tools started.');
      } catch (e) {
        log('[ERROR] Error starting CS2 tools: ' + e);
      }
    }

    function openFileConverterPrompt() {
      const p = prompt("Enter full path to audio file on your PC to convert to clean 44.1kHz MP3:");
      if (!p) return;
      log(`Converting audio file: ${p}...`);
      fetch('/api/convert_mp3', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path: p})
      })
      .then(r => r.json())
      .then(d => {
        log(d.output || 'Conversion complete.');
        alert(d.output || 'Conversion complete.');
      })
      .catch(e => log('[ERROR] Conversion error: ' + e));
    }

    // Initial Load
    window.onload = () => {
      refreshServices();
      loadAnnouncements();
    };
  </script>
</body>
</html>
"""

# Common convars list with descriptions
POPULAR_CONVARS = [
    {"name": "mp_roundtime_defuse", "desc": "Round time for defuse maps (minutes)", "default": "1.92"},
    {"name": "mp_roundtime", "desc": "General round time (minutes)", "default": "1.92"},
    {"name": "mp_maxrounds", "desc": "Total match rounds (e.g. 24 for MR12)", "default": "24"},
    {"name": "mp_freezetime", "desc": "Round start freeze time (seconds)", "default": "15"},
    {"name": "mp_buytime", "desc": "Buy time in seconds", "default": "20"},
    {"name": "mp_startmoney", "desc": "Starting cash", "default": "800"},
    {"name": "mp_maxmoney", "desc": "Max cash player can hold", "default": "16000"},
    {"name": "mp_c4timer", "desc": "Bomb explosion timer (seconds)", "default": "40"},
    {"name": "mp_warmuptime", "desc": "Warmup duration (seconds)", "default": "60"},
    {"name": "mp_friendlyfire", "desc": "Friendly fire (1 = on, 0 = off)", "default": "0"},
    {"name": "mp_overtime_enable", "desc": "Enable overtime on tie (1 = on, 0 = off)", "default": "1"},
    {"name": "mp_overtime_maxrounds", "desc": "Rounds per overtime", "default": "6"},
    {"name": "mp_halftime", "desc": "Switch teams at halftime", "default": "1"},
    {"name": "mp_match_can_clinch", "desc": "End match early if win clinched", "default": "1"}
]

class ControlCenterHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress noisy request logs

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
            return

        if self.path == "/api/status":
            info = a2s_info()
            self.send_json(info)
            return

        if self.path == "/api/announcements":
            try:
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_ANNOUNCER_PATH, 'r') as f:
                    raw = f.read().decode('utf-8')
                sftp.close()
                ssh.close()
                clean_lines = [l for l in raw.splitlines() if not l.strip().startswith("//")]
                data = json.loads("\n".join(clean_lines))
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e), "IntervalSeconds": 90, "RandomOrder": True, "Prefix": "{Gold}★ {LightBlue}[Walliez]{Default}", "Messages": []})
            return

        if self.path == "/api/hostname":
            try:
                info = a2s_info()
                hostname = info.get("name", "")
                if not hostname:
                    ssh = get_ssh_client()
                    _, stdout, _ = ssh.exec_command(f'grep -E "^[[:space:]]*hostname" {REMOTE_SERVER_CFG}')
                    line = stdout.read().decode('utf-8').strip()
                    ssh.close()
                    m = re.search(r'hostname\s+["\'](.*?)["\']', line)
                    hostname = m.group(1) if m else "Counter-Strike 2 Server"
                self.send_json({"hostname": hostname})
            except Exception as e:
                self.send_json({"hostname": "Counter-Strike 2 Server", "error": str(e)})
            return

        if self.path == "/api/convars":
            # Query live convars via RCON
            results = []
            for item in POPULAR_CONVARS:
                val = rcon_exec(item["name"])
                clean_val = item["default"]
                if val:
                    # Parse 'convar = "val"'
                    m = re.search(r'=\s*"?([^\s"]+)"?', val)
                    if m:
                        clean_val = m.group(1)
                results.append({"name": item["name"], "desc": item["desc"], "value": clean_val})
            self.send_json(results)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if self.path == "/api/announcements":
            try:
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_ANNOUNCER_PATH, 'w') as f:
                    json.dump(req_data, f, indent=2)
                sftp.close()
                ssh.close()
                # Reload via RCON
                reload_out = rcon_exec("css_plugins reload ServerAnnouncer")
                self.send_json({"success": True, "rcon": reload_out})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/hostname":
            new_name = req_data.get("hostname", "").strip()
            if not new_name:
                self.send_json({"success": False, "error": "Empty hostname"})
                return
            try:
                # 1. Apply via RCON live
                rcon_exec(f'hostname "{new_name}"')
                # 2. Save in server.cfg permanently
                ssh = get_ssh_client()
                sftp = ssh.open_sftp()
                with sftp.open(REMOTE_SERVER_CFG, 'r') as f:
                    content = f.read().decode('utf-8')
                if re.search(r'^[ \t]*hostname\s+.*$', content, flags=re.MULTILINE):
                    new_content = re.sub(r'^[ \t]*hostname\s+.*$', f'hostname "{new_name}"', content, flags=re.MULTILINE)
                else:
                    new_content = f'hostname "{new_name}"\n' + content
                with sftp.open(REMOTE_SERVER_CFG, 'w') as f:
                    f.write(new_content)
                sftp.close()
                ssh.close()
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/convars":
            try:
                ssh = get_ssh_client()
                for cname, cval in req_data.items():
                    rcon_exec(f'{cname} {cval}')
                    # Also append/update in gamemode_competitive_server.cfg
                    cmd = f'sed -i "/^{cname}/d" {REMOTE_COMP_CFG} && echo "{cname} {cval}" >> {REMOTE_COMP_CFG}'
                    ssh.exec_command(cmd)
                ssh.close()
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/service/action":
            action = req_data.get("action")
            ssh = get_ssh_client()
            if action == "restart_cs2":
                _, stdout, _ = ssh.exec_command("systemctl restart cs2 && sleep 2 && systemctl status cs2 --no-pager")
                out = stdout.read().decode('utf-8', errors='replace')
            elif action == "restart_bot":
                _, stdout, _ = ssh.exec_command("systemctl restart cs2-discord-bot && sleep 2 && systemctl status cs2-discord-bot --no-pager")
                out = stdout.read().decode('utf-8', errors='replace')
            elif action == "reload_plugins":
                out = rcon_exec("css_plugins reload")
            else:
                out = "Unknown action"
            ssh.close()
            self.send_json({"success": True, "output": out})
            return

        if self.path == "/api/sync_client":
            try:
                proc = subprocess.run([sys.executable, "sync_client_anthems.py"], capture_output=True, text=True, timeout=30)
                self.send_json({"success": True, "output": proc.stdout or proc.stderr})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/convert_mp3":
            audio_path = req_data.get("path", "").strip(' "\'')
            if not os.path.exists(audio_path):
                self.send_json({"success": False, "error": "File does not exist on disk."})
                return
            try:
                proc = subprocess.run([sys.executable, "export_clean_mp3.py", audio_path], capture_output=True, text=True, timeout=30)
                self.send_json({"success": True, "output": proc.stdout or proc.stderr})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/launch_visual_studio":
            try:
                subprocess.Popen([sys.executable, "add_mvp_ui.py"])
                self.send_json({"success": True, "message": "Visual MVP Web Studio started on http://localhost:5500"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/rebuild_workshop":
            try:
                proc = subprocess.run([sys.executable, "prepare_workshop_mvp.py", "--no-prompt"], capture_output=True, text=True, timeout=180)
                self.send_json({"success": True, "output": proc.stdout or proc.stderr})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        if self.path == "/api/launch_workshop_tools":
            try:
                cs2_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
                if os.path.exists(cs2_exe):
                    subprocess.Popen([cs2_exe, "-tools", "-addon", "wlzMVP"])
                    self.send_json({"success": True, "message": "CS2 Workshop Tools launched."})
                else:
                    self.send_json({"success": False, "error": "cs2.exe not found at standard Steam path."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
            return

        self.send_response(404)
        self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def open_app_window(url):
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.path.exists(edge_path):
        try:
            subprocess.Popen([edge_path, f"--app={url}"])
            return
        except Exception:
            pass
    webbrowser.open(url)

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    port = 5890
    server = HTTPServer(("127.0.0.1", port), ControlCenterHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("        CS2 Server Control Center (Active)")
    print("=" * 65)
    print(f"[*] Server Control Center running at: {url}")
    print("[*] Launching native application window...")
    open_app_window(url)
    print("[*] Press Ctrl+C in this terminal window to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Control Center closed gracefully.")

if __name__ == "__main__":
    main()
