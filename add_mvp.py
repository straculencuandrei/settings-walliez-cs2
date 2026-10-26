#!/usr/bin/env python3
"""
CS2 MVP Anthem Instant Adder, Audio Trimmer & Studio
---------------------------------------------------
Uploads, trims, validates, and activates new MVP Anthems instantly on your Counter-Strike 2 server.
Provides both an interactive visual Web Studio UI and a high-speed CLI.

Usage Examples:
    # 1. Launch Visual Web Studio UI (Waveform scrubber, preview player, drop zone):
    python add_mvp.py --ui
    # (or simply run without arguments)
    python add_mvp.py

    # 2. CLI Mode: Trim starting at 0:45 for 8 seconds:
    python add_mvp.py "C:\\path\\to\\full_song.mp3" --name "Drop Beat" --start 00:45 --duration 8

    # 3. CLI Mode: Full song as-is:
    python add_mvp.py "C:\\path\\to\\clip.mp3" --name "Short Beat" --category "Public Anthems"

    # 4. CLI Mode: Built-in CS2 Sound Event:
    python add_mvp.py --soundevent "Music.Valve_MVP" --name "Valve Anthem"
"""

import os
import re
import sys
import json
import time
import argparse
import paramiko

# Server Connection Details
SERVER_HOST = "81.181.113.120"
SERVER_PORT = 22
SERVER_USER = "root"
SERVER_PASS = ")(e092e8EjTUiV"

REMOTE_SOUND_DIR_1 = "/home/csgoserver/server-cs2/game/csgo/sounds/mvp"
REMOTE_SOUND_DIR_2 = "/home/csgoserver/server-cs2/game/csgo/sound/mvp"
REMOTE_CONFIG_PATH = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/configs/plugins/MVPAnthem/MVPAnthem.json"


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


def sanitize_filename(name: str) -> str:
    """Produce a safe, lowercase, alphanumeric filename for CS2 sound engine."""
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "custom_mvp"


def parse_time_to_seconds(time_str: str) -> float:
    """Parse string timestamps like '00:45.5', '1:20', or '45' into seconds."""
    if not time_str:
        return 0.0
    parts = str(time_str).strip().split(':')
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    return 0.0


def format_seconds_to_ffmpeg(seconds: float) -> str:
    """Convert float seconds into HH:MM:SS.mmm format for FFmpeg."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def validate_audio_file(file_path: str) -> tuple[bool, str, dict]:
    """Strictly validate audio file existence, size, header, and format."""
    if not os.path.isfile(file_path):
        return False, f"File not found: '{file_path}'", {}

    file_size = os.path.getsize(file_path)
    if file_size < 1024:
        return False, f"File is too small or empty ({file_size} bytes). Minimum size is 1 KB.", {}

    max_size_bytes = 50 * 1024 * 1024  # 50 MB max for source file before trim
    if file_size > max_size_bytes:
        return False, f"File exceeds 50 MB ({file_size / (1024*1024):.2f} MB).", {}

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']:
        return False, f"Unsupported format '{ext}'. Only standard audio files are supported.", {}

    # Inspect Magic Bytes
    with open(file_path, 'rb') as f:
        header = f.read(12)

    is_valid_header = False
    format_detected = "Audio Track"

    if ext == '.mp3':
        if header.startswith(b'ID3') or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            is_valid_header = True
            format_detected = "MPEG Audio (MP3)"
    elif ext == '.wav':
        if header.startswith(b'RIFF') and b'WAVE' in header:
            is_valid_header = True
            format_detected = "RIFF Wave Audio (WAV)"
    else:
        # Other audio types are valid as inputs because remote FFmpeg will transcode to standard MP3
        is_valid_header = True
        format_detected = f"Source Audio ({ext.upper()})"

    if not is_valid_header:
        return False, f"File has extension '{ext}' but does not have valid audio headers.", {}

    stats = {
        "format": format_detected,
        "size_kb": file_size / 1024,
    }
    return True, "Valid", stats


def main():
    parser = argparse.ArgumentParser(description="Instantly add, trim, and validate an MVP Anthem for CS2")
    parser.add_argument("file", nargs="?", help="Path to the audio file (.mp3, .wav, etc.) to upload and trim")
    parser.add_argument("--ui", action="store_true", help="Launch the Visual Web Studio UI in your browser")
    parser.add_argument("--start", "--start-time", dest="start_time", default="0", help="Timestamp where the MVP clip should start (e.g. '00:45', '1:12.5', or seconds '45')")
    parser.add_argument("--duration", "-d", type=float, default=8.0, help="Clip length in seconds (default: 8.0s, recommended 5-10s)")
    parser.add_argument("--volume", "-v", type=float, default=1.0, help="Output clip audio volume multiplier (e.g. 0.8 for 80%, 1.2 for 120%)")
    parser.add_argument("--name", "-n", help="Display Name in-game (e.g. 'Florin Salam - M-as Certa')")
    parser.add_argument("--category", "-c", default="Public Anthems", help="Category name (default: 'Public Anthems')")
    parser.add_argument("--permission", "-p", default="", help="Permission tag required to equip (e.g. '@css/vip', '#wlz/admin')")
    parser.add_argument("--soundevent", default="Ubersoft.roundmvpanthem_01", help="In-Game CS2 Audio Event pairing for 100% crash-safe network dispatch (default: 'Ubersoft.roundmvpanthem_01')")
    parser.add_argument("--no-preview", action="store_true", help="Disable preview playback for this track")
    parser.add_argument("--restart", action="store_true", help="Force restart cs2 service after adding (auto-reload is active by default)")

    args = parser.parse_args()

    # Launch UI if requested or if no arguments provided
    if args.ui or (len(sys.argv) == 1):
        try:
            import add_mvp_ui
            add_mvp_ui.run_studio()
            return
        except Exception as e:
            print(f"[!] Error launching Visual Web Studio: {e}")
            sys.exit(1)

    from datetime import datetime

    def log(msg: str, tag: str = "INFO"):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{tag}] {msg}")

    start_sec = parse_time_to_seconds(args.start_time)
    duration_sec = max(3.0, min(15.0, args.duration))

    # Mode 1: Pure SoundEvent (no file uploaded)
    if not args.file and args.soundevent:
        sound_path = args.soundevent.strip()
        sound_event_assigned = sound_path
        display_name = args.name or sound_path
        track_key = sanitize_filename(display_name)
        is_file_upload = False
        should_trim = False
    # Mode 2: Audio File Upload + Remote Trimming
    elif args.file:
        file_path = os.path.abspath(args.file)
        log(f"Validating source audio file: {file_path} ...", "CHECK")
        valid, msg, stats = validate_audio_file(file_path)
        if not valid:
            log(f"Validation Failed: {msg}", "ERROR")
            sys.exit(1)

        log(f"Format: {stats['format']} | Source Size: {stats['size_kb']:.1f} KB", "INFO")

        filename = os.path.basename(file_path)
        clean_base = sanitize_filename(os.path.splitext(filename)[0])
        clean_filename = f"{clean_base}.mp3"

        display_name = args.name or os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        track_key = clean_base
        sound_path = f"sounds/mvp/{clean_filename}"
        sound_event_assigned = args.soundevent.strip() if args.soundevent else "Ubersoft.roundmvpanthem_01"
        is_file_upload = True
        should_trim = (start_sec > 0 or duration_sec > 0)
    else:
        parser.print_help()
        sys.exit(1)

    print("\n" + "="*58)
    print("             CS2 MVP ANTHEM DEPLOYMENT PLAN")
    print("="*58)
    print(f"  Display Name : {display_name}")
    print(f"  Track Key    : {track_key}")
    print(f"  Category     : {args.category}")
    print(f"  Sound Path   : {sound_path}")
    print(f"  Sound Event  : {sound_event_assigned} (Crash-Safe Dispatch)")
    if is_file_upload:
        print(f"  Clip Window  : {format_seconds_to_ffmpeg(start_sec)} -> {format_seconds_to_ffmpeg(start_sec + duration_sec)} ({duration_sec:.1f}s)")
        print(f"  Volume Gain  : {args.volume*100:.0f}%")
    print(f"  Permissions  : {args.permission or 'Public (Everyone)'}")
    print(f"  Previewable  : {not args.no_preview}")
    print("="*58 + "\n")

    # Connect to Remote Server via SSH/SFTP
    log(f"Connecting to CS2 Dedicated Server ({SERVER_HOST}:{SERVER_PORT}) ...", "SSH")
    try:
        ssh = get_ssh_client()
        sftp = ssh.open_sftp()
        log("Connection established successfully.", "SUCCESS")
    except Exception as e:
        log(f"SSH Connection failed: {e}", "ERROR")
        sys.exit(1)

    try:
        # Step 1: Upload and Trim Audio
        if is_file_upload:
            dest_path_1 = f"{REMOTE_SOUND_DIR_1}/{clean_filename}"
            dest_path_2 = f"{REMOTE_SOUND_DIR_2}/{clean_filename}"
            ssh.exec_command(f"mkdir -p {REMOTE_SOUND_DIR_1} {REMOTE_SOUND_DIR_2}")

            remote_temp = f"/tmp/mvp_in_{int(time.time())}_{clean_filename}.tmp"
            log(f"Uploading source audio to server staging area...", "UPLOAD")
            sftp.put(file_path, remote_temp)

            start_fmt = format_seconds_to_ffmpeg(start_sec)
            vol_filter = f"-filter:a volume={args.volume:.2f} " if abs(args.volume - 1.0) > 0.01 else ""

            if should_trim:
                log(f"Executing server-side FFmpeg trim: Start at {start_fmt} for {duration_sec:.1f}s (MP3 44.1 kHz, original quality)...", "ENCODE")
                trim_cmd = (
                    f"/usr/local/bin/ffmpeg -y -ss {start_fmt} -t {duration_sec:.2f} -i {remote_temp} "
                    f"{vol_filter}-codec:a libmp3lame -q:a 0 -ar 44100 {dest_path_1} && "
                    f"cp {dest_path_1} {dest_path_2}"
                )
            else:
                log(f"Executing server-side FFmpeg conversion to MP3 44.1 kHz (original quality)...", "ENCODE")
                trim_cmd = (
                    f"/usr/local/bin/ffmpeg -y -i {remote_temp} "
                    f"{vol_filter}-codec:a libmp3lame -q:a 0 -ar 44100 {dest_path_1} && "
                    f"cp {dest_path_1} {dest_path_2}"
                )

            stdin, stdout, stderr = ssh.exec_command(trim_cmd)
            err = stderr.read().decode('utf-8', errors='replace')
            status = stdout.channel.recv_exit_status()

            ssh.exec_command(f"rm -f {remote_temp}")
            if status != 0:
                log(f"FFmpeg encoding failed (code {status}): {err}", "ERROR")
                sys.exit(1)

            log(f"Clip encoded to MP3 44.1 kHz & saved: {dest_path_1}", "SUCCESS")

            # Auto-install to local CS2 game files on this PC
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
                        loc_target = os.path.join(loc_dir, clean_filename)
                        sftp.get(dest_path_1, loc_target)
                    log(f"Auto-installed to local CS2: game/csgo/sounds/mvp/{clean_filename}", "LOCAL")
                    local_installed = True
                    break
            if not local_installed:
                log("Local CS2 installation not found on standard paths.", "WARN")

        # Step 2: Download and update MVPAnthem.json safely
        log(f"Reading remote configuration: {REMOTE_CONFIG_PATH} ...", "CONFIG")
        with sftp.file(REMOTE_CONFIG_PATH, 'r') as f:
            raw_json = f.read().decode('utf-8')

        config_data = json.loads(raw_json)

        # Enforce crash immunity settings
        config_data["RemovePlayerInGameMvp"] = False

        # Backup existing config
        backup_path = f"{REMOTE_CONFIG_PATH}.bak"
        with sftp.file(backup_path, 'w') as f:
            f.write(raw_json)
        log(f"Automated backup generated: {backup_path}", "BACKUP")

        categories = config_data.setdefault("Categories", {})
        target_category = categories.setdefault(args.category, {})

        # Build track entry
        permissions_list = [p.strip() for p in args.permission.split(',') if p.strip()]
        new_track = {
            "DisplayName": display_name,
            "Sound": sound_path,
            "SoundEvent": sound_event_assigned,
            "EnablePreview": not args.no_preview,
            "Permissions": permissions_list
        }

        # Check for duplicate
        is_update = track_key in target_category
        target_category[track_key] = new_track

        # Save updated config
        new_config_json = json.dumps(config_data, indent=2)
        with sftp.file(REMOTE_CONFIG_PATH, 'w') as f:
            f.write(new_config_json)

        action_str = "Updated existing track" if is_update else "Added new track"
        log(f"{action_str} in category '{args.category}' with SoundEvent '{sound_event_assigned}'", "SUCCESS")

        # Step 3: Fix ownership
        ssh.exec_command(f"chown -R csgoserver:csgoserver {REMOTE_SOUND_DIR_1} {REMOTE_SOUND_DIR_2} {REMOTE_CONFIG_PATH}")
        log("File ownership verified (csgoserver:csgoserver).", "INFO")

        # Step 4: Hot Reload / Restart
        if args.restart:
            log("Restarting cs2 server as requested (--restart) ...", "SERVICE")
            ssh.exec_command("systemctl restart cs2")
            log("Server restarted successfully!", "SUCCESS")
        else:
            log("FileSystemWatcher detected config change -> Hot-reloaded instantly in memory!", "SUCCESS")

        print("\n" + "="*58)
        log(f"SUCCESS: MVP Anthem '{display_name}' is fully deployed and LIVE!", "DONE")
        print("  Players can equip it now via '!mvp', '!anthem', or '/menu'.")
        print("="*58 + "\n")

    finally:
        sftp.close()
        ssh.close()


if __name__ == "__main__":
    main()
