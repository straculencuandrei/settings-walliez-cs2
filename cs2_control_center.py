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

# HTML Template with modern Dark Glassmorphism UI
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS2 Server Control Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(17, 24, 39, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --accent: #818cf8;
      --success: #22c55e;
      --warning: #facc15;
      --danger: #ef4444;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(129, 140, 248, 0.08) 0px, transparent 50%);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }
    /* Header */
    header {
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      padding: 14px 24px;
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
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #0284c7, #6366f1);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(34, 197, 94, 0.12);
      border: 1px solid rgba(34, 197, 94, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 600;
      color: #4ade80;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 10px #22c55e;
    }

    /* Main Container & Tabs */
    .app-container {
      max-width: 1200px;
      margin: 0 auto;
      width: 100%;
      padding: 24px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .nav-tabs {
      display: flex;
      gap: 8px;
      background: rgba(15, 23, 42, 0.6);
      padding: 6px;
      border-radius: 14px;
      border: 1px solid var(--card-border);
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.9rem;
      font-weight: 600;
      padding: 10px 18px;
      border-radius: 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text);
      background: rgba(255, 255, 255, 0.04);
    }
    .tab-btn.active {
      color: #fff;
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.6), rgba(99, 102, 241, 0.6));
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
    }

    /* Content Cards */
    .tab-content { display: none; }
    .tab-content.active { display: block; animation: fadeIn 0.25s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(10px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      margin-bottom: 20px;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
    }
    .card-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* Forms & Controls */
    .form-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    input[type="text"], input[type="number"], textarea, select {
      width: 100%;
      background: rgba(3, 7, 18, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 12px 14px;
      color: #fff;
      font-family: inherit;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }
    .input-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: #fff;
      border: none;
      border-radius: 10px;
      padding: 12px 20px;
      font-weight: 600;
      font-size: 0.92rem;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
    }
    .btn:hover {
      background: linear-gradient(135deg, #0369a1, #1d4ed8);
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: none;
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.14);
    }
    .btn-danger {
      background: linear-gradient(135deg, #dc2626, #b91c1c);
      box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
    }
    .btn-danger:hover {
      background: #991b1b;
    }
    .btn-sm {
      padding: 6px 12px;
      font-size: 0.8rem;
      border-radius: 8px;
    }

    /* Message Item List */
    .msg-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 20px;
    }
    .msg-item {
      background: rgba(3, 7, 18, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .msg-text-box {
      flex: 1;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.88rem;
      color: #e2e8f0;
      word-break: break-all;
    }
    .msg-actions {
      display: flex;
      gap: 8px;
    }

    /* CS2 In-Game Chat Simulator */
    .cs2-chat-sim {
      background: rgba(0, 0, 0, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 10px;
      padding: 16px;
      font-family: 'Segoe UI', Tahoma, sans-serif;
      font-size: 0.95rem;
      min-height: 80px;
      display: flex;
      align-items: center;
      margin-top: 10px;
      box-shadow: inset 0 2px 6px rgba(0,0,0,0.6);
    }
    .cs2-chat-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.06em;
      color: #64748b;
      margin-bottom: 6px;
    }
    .cs2-preview-text {
      color: #ffffff;
      line-height: 1.4;
      font-weight: 500;
    }

    /* Terminal Output Drawer */
    .terminal-drawer {
      background: #030712;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      max-height: 160px;
      overflow-y: auto;
      color: #a7f3d0;
      box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
      white-space: pre-wrap;
    }

    /* Color Palette Tags Pill */
    .color-tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }
    .color-tag-pill {
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.06);
      cursor: pointer;
      border: 1px solid rgba(255, 255, 255, 0.1);
      transition: background 0.15s;
    }
    .color-tag-pill:hover { background: rgba(255, 255, 255, 0.15); }
    
    /* Grid for quick stats */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
    }
    .stat-label { font-size: 0.8rem; color: var(--text-muted); font-weight: 600; }
    .stat-val { font-size: 1.3rem; font-weight: 700; color: #fff; margin-top: 4px; }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">⚡</div>
      <div>
        <div class="brand-title">CS2 Server Control Center</div>
        <div style="font-size: 0.75rem; color: #64748b;">Host: 81.181.113.120:27015 • talent.walliez.xyz</div>
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
      <button class="tab-btn active" onclick="switchTab('tab-announcements')">📢 In-Game Announcements</button>
      <button class="tab-btn" onclick="switchTab('tab-hostname')">🏷️ Server Name & Hostname</button>
      <button class="tab-btn" onclick="switchTab('tab-convars')">⚙️ Match Settings & Convars</button>
      <button class="tab-btn" onclick="switchTab('tab-mvp')">🎵 MVP Anthems & FastDL</button>
      <button class="tab-btn" onclick="switchTab('tab-services')">📊 Services & Discord Bot</button>
    </div>

    <!-- TAB 1: Announcements Manager -->
    <div id="tab-announcements" class="tab-content active">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">📢 ServerAnnouncer Settings</div>
            <div class="card-desc">Scheduled in-game chat messages promoting skinz, mvpz, and community links.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadAnnouncements()">🔄 Reload from Server</button>
        </div>

        <div class="input-row">
          <div class="form-group">
            <label>Interval Between Announcements (Seconds)</label>
            <input type="number" id="announcerInterval" min="15" max="600" value="90">
          </div>
          <div class="form-group">
            <label>Rotation Mode</label>
            <select id="announcerRandom">
              <option value="true">Random Order (Non-Repeating)</option>
              <option value="false">Sequential Order (In List Order)</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Announcement Prefix</label>
          <input type="text" id="announcerPrefix" value="{Gold}★ {LightBlue}[Walliez]{Default}" oninput="updateChatPreview()">
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

        <div class="card-header" style="margin-top: 24px; margin-bottom: 12px;">
          <div class="card-title" style="font-size: 1rem;">Active Announcement Messages</div>
          <button class="btn btn-sm" onclick="addNewMessagePrompt()">➕ Add New Message</button>
        </div>

        <div class="msg-list" id="announcementsList">
          <div style="color: var(--text-muted); font-size: 0.9rem;">Loading messages...</div>
        </div>

        <div class="cs2-chat-label">🎮 Live CS2 In-Game Chat Simulator Preview:</div>
        <div class="cs2-chat-sim">
          <div class="cs2-preview-text" id="cs2ChatSimPreview">Previewing announcement...</div>
        </div>

        <div style="margin-top: 24px; display: flex; justify-content: flex-end; gap: 12px;">
          <button class="btn btn-secondary" onclick="loadAnnouncements()">Cancel Changes</button>
          <button class="btn" onclick="saveAnnouncementsToServer()">🚀 Save & Deploy to Live Server</button>
        </div>
      </div>
    </div>

    <!-- TAB 2: Server Hostname & Title -->
    <div id="tab-hostname" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">🏷️ Server Hostname / Title Manager</div>
            <div class="card-desc">Instantly updates the live CS2 server name via RCON and saves permanently to server.cfg.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadHostname()">🔄 Query Live Name</button>
        </div>

        <div class="form-group">
          <label>Server Hostname</label>
          <input type="text" id="serverHostnameInput" placeholder="Counter-Strike 2 Server" oninput="updateHostnamePreview()">
        </div>

        <div class="cs2-chat-label" style="margin-top: 16px;">Steam & CS2 Server Browser Preview:</div>
        <div style="background: rgba(3,7,18,0.7); border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; padding: 16px;">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="font-weight: 700; font-size: 1.05rem; color: #fff;" id="hostnamePreviewText">talent.walliez.xyz</div>
            <div style="font-size: 0.85rem; color: #4ade80; font-weight: 600;">🟢 Online • 81.181.113.120:27015</div>
          </div>
        </div>

        <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveHostname()">💾 Apply Hostname Immediately</button>
        </div>
      </div>
    </div>

    <!-- TAB 3: Match Settings & Convars -->
    <div id="tab-convars" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">⚙️ Match Settings & Convar Editor</div>
            <div class="card-desc">Quickly tune round timers, overtime, economy, and game rules.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="loadConvars()">🔄 Fetch from Server</button>
        </div>

        <div class="form-group">
          <input type="text" id="convarSearch" placeholder="🔍 Search convar or description..." oninput="filterConvars()">
        </div>

        <div id="convarsGrid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px;">
          <!-- Populated by JS -->
        </div>

        <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
          <button class="btn" onclick="saveConvars()">💾 Apply Convar Settings</button>
        </div>
      </div>
    </div>

    <!-- TAB 4: MVP Anthems & FastDL -->
    <div id="tab-mvp" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">🎵 MVP Anthem Studio & Audio Converter</div>
            <div class="card-desc">Convert, sync, and deploy custom music pack anthems to the CS2 server and local game files.</div>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Workshop Addon</div>
            <div class="stat-val" style="font-size: 1.1rem; color: #38bdf8;">wlzMVP (3827657422)</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">FastDL URL</div>
            <div class="stat-val" style="font-size: 0.95rem; color: #a7f3d0;">http://81.181.113.120/fastdl/</div>
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 10px;">
          <div style="background: rgba(3,7,18,0.5); padding: 18px; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; color: #fff;">Launch Visual MVP Web Studio</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">Visual waveform scrubber, player preview, trim controls, and 1-click deployment.</div>
            </div>
            <button class="btn" onclick="launchVisualStudio()">🚀 Open Visual Studio</button>
          </div>

          <div style="background: rgba(3,7,18,0.5); padding: 18px; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; color: #fff;">1-Click Local Client Sync</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">Sync all server MVP Anthems directly to your local Counter-Strike 2 Steam library.</div>
            </div>
            <button class="btn btn-secondary" onclick="triggerClientSync()">🔄 Sync Local CS2</button>
          </div>

          <div style="background: rgba(3,7,18,0.5); padding: 18px; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; color: #fff;">Convert Audio to Clean 44.1kHz MP3</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">Uses the exact onlineaudioconverter.com 320kbps 44.1kHz CBR algorithm with metadata stripped.</div>
            </div>
            <button class="btn btn-secondary" onclick="openFileConverterPrompt()">📁 Convert Audio File</button>
          </div>

          <div style="background: rgba(3,7,18,0.5); padding: 18px; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; color: #fff;">Rebuild & Deploy Workshop Addon (wlzMVP)</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">Compiles all staged tracks to vsnd_c, generates VPK, and uploads to dedicated server cache.</div>
            </div>
            <button class="btn btn-secondary" onclick="triggerWorkshopRebuild()">🔨 Rebuild Workshop Addon</button>
          </div>

          <div style="background: rgba(3,7,18,0.5); padding: 18px; border-radius: 12px; border: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <div style="font-weight: 600; color: #fff;">Launch CS2 Workshop Tools</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">Opens the official Counter-Strike 2 Workshop Tools editor with the wlzMVP addon loaded.</div>
            </div>
            <button class="btn btn-secondary" onclick="launchWorkshopTools()">🛠️ Launch CS2 Tools</button>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 5: Services & Discord Bot -->
    <div id="tab-services" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">📊 VPS Services & Discord Bot Monitor</div>
            <div class="card-desc">Control server services, restart processes, and check status.</div>
          </div>
          <button class="btn btn-sm btn-secondary" onclick="refreshServices()">🔄 Refresh Status</button>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">CS2 Game Server</div>
            <div class="stat-val" id="statCs2Status" style="color: #4ade80;">Active (Running)</div>
            <button class="btn btn-sm btn-danger" style="margin-top: 10px;" onclick="serviceAction('restart_cs2')">Restart CS2 Server</button>
          </div>
          <div class="stat-card">
            <div class="stat-label">Discord 24/7 Bot</div>
            <div class="stat-val" id="statBotStatus" style="color: #4ade80;">Active (Running)</div>
            <button class="btn btn-sm btn-secondary" style="margin-top: 10px;" onclick="serviceAction('restart_bot')">Restart Discord Bot</button>
          </div>
          <div class="stat-card">
            <div class="stat-label">CSS Plugins Core</div>
            <div class="stat-val" style="color: #38bdf8;">12 Plugins Loaded</div>
            <button class="btn btn-sm btn-secondary" style="margin-top: 10px;" onclick="serviceAction('reload_plugins')">Hot Reload All Plugins</button>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Direct Panel Links:</div>
          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="https://skinz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none;">🗡️ Skin & Knife Web Panel</a>
            <a href="https://mvpz.walliez.xyz" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none;">🎵 MVP Anthems Panel</a>
            <a href="https://skinz.walliez.xyz/connect/" target="_blank" class="btn btn-secondary btn-sm" style="text-decoration: none;">🎮 1-Click Steam Connect</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Terminal Activity Drawer -->
    <div class="card" style="padding: 16px; margin-bottom: 0;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">💻 Operation Log:</div>
        <button class="btn btn-sm btn-secondary" style="padding: 2px 8px; font-size: 0.75rem;" onclick="clearLogs()">Clear</button>
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
      let currentColor = '#FFFFFF';
      for (const [tag, hex] of Object.entries(CS2_COLORS)) {
        html = html.split(tag).join(`</span><span style="color:${hex};">`);
      }
      return `<span>${html}</span>`;
    }

    // Announcements state
    let announcementsData = {
      IntervalSeconds: 90,
      RandomOrder: true,
      Prefix: "{Gold}★ {LightBlue}[Walliez]{Default}",
      Messages: []
    };

    async function loadAnnouncements() {
      log('Fetching announcements configuration from VPS...');
      try {
        const res = await fetch('/api/announcements');
        announcementsData = await res.json();
        document.getElementById('announcerInterval').value = announcementsData.IntervalSeconds || 90;
        document.getElementById('announcerRandom').value = announcementsData.RandomOrder ? "true" : "false";
        document.getElementById('announcerPrefix').value = announcementsData.Prefix || "{Gold}★ {LightBlue}[Walliez]{Default}";
        renderAnnouncementsList();
        log('Announcements loaded successfully.');
      } catch (e) {
        log('Error loading announcements: ' + e);
      }
    }

    function renderAnnouncementsList() {
      const container = document.getElementById('announcementsList');
      container.innerHTML = '';
      if (!announcementsData.Messages || announcementsData.Messages.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">No messages currently configured.</div>';
        updateChatPreview();
        return;
      }
      announcementsData.Messages.forEach((msg, idx) => {
        const item = document.createElement('div');
        item.className = 'msg-item';
        item.innerHTML = `
          <div class="msg-text-box">
            <span style="color:#64748b; font-weight:700; margin-right:8px;">#${idx+1}</span>
            <span>${msg}</span>
          </div>
          <div class="msg-actions">
            <button class="btn btn-sm btn-secondary" onclick="editMessagePrompt(${idx})">✏️ Edit</button>
            <button class="btn btn-sm btn-danger" onclick="deleteMessage(${idx})">🗑️ Delete</button>
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
          log('✅ Announcements successfully saved and ServerAnnouncer hot-reloaded via RCON!');
          alert('Announcements successfully deployed and live on the server!');
        } else {
          log('❌ Error saving announcements: ' + out.error);
        }
      } catch (e) {
        log('❌ Request failed: ' + e);
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
        log('Error querying hostname: ' + e);
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
          log('✅ Hostname updated immediately in live server & server.cfg!');
          alert('Hostname applied successfully!');
        } else {
          log('❌ Error: ' + out.error);
        }
      } catch (e) {
        log('❌ Request failed: ' + e);
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
        log('Error loading convars: ' + e);
      }
    }

    function renderConvars(convars) {
      const grid = document.getElementById('convarsGrid');
      grid.innerHTML = '';
      convars.forEach(item => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
          <div style="font-weight:700; color:#38bdf8; font-size:0.9rem;">${item.name}</div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:8px;">${item.desc}</div>
          <input type="text" id="cv_${item.name}" value="${item.value}">
        `;
        grid.appendChild(card);
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
        log('✅ Convars applied successfully via RCON!');
        alert('Convar settings updated live on the server!');
      } catch (e) {
        log('Error applying convars: ' + e);
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
        log('Action error: ' + e);
      }
    }

    async function refreshServices() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('headerStatusText').innerText = data.online ? `Online (${data.players}/${data.max_players})` : 'Offline';
        document.getElementById('statCs2Status').innerText = data.online ? `Active (${data.map})` : 'Stopped';
        document.getElementById('statCs2Status').style.color = data.online ? '#4ade80' : '#ef4444';
      } catch (e) {}
    }

    async function triggerClientSync() {
      log('Running 1-click client anthem sync...');
      try {
        const res = await fetch('/api/sync_client', { method: 'POST' });
        const out = await res.json();
        log(out.output || 'Sync completed.');
        alert('Local CS2 client sync finished!');
      } catch (e) {
        log('Sync error: ' + e);
      }
    }

    async function launchVisualStudio() {
      log('Launching Visual MVP Web Studio...');
      try {
        const res = await fetch('/api/launch_visual_studio', { method: 'POST' });
        const out = await res.json();
        log(out.message || 'Visual MVP Studio launched.');
      } catch (e) {
        log('Error launching studio: ' + e);
      }
    }

    async function triggerWorkshopRebuild() {
      if (!confirm('Rebuild all staged anthems, compile to vsnd_c, and deploy VPK to server?')) return;
      log('Building and compiling Workshop Addon wlzMVP... (this may take 20-40s)');
      try {
        const res = await fetch('/api/rebuild_workshop', { method: 'POST' });
        const out = await res.json();
        log(out.output || 'Rebuild complete.');
        alert('Workshop Addon rebuilt and deployed to server!');
      } catch (e) {
        log('Error rebuilding addon: ' + e);
      }
    }

    async function launchWorkshopTools() {
      log('Launching Counter-Strike 2 Workshop Tools for wlzMVP...');
      try {
        const res = await fetch('/api/launch_workshop_tools', { method: 'POST' });
        const out = await res.json();
        log(out.message || 'CS2 Tools started.');
      } catch (e) {
        log('Error starting CS2 tools: ' + e);
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
        alert(d.output || 'Conversion complete!');
      })
      .catch(e => log('Conversion error: ' + e));
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
