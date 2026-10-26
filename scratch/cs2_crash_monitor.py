#!/usr/bin/env python3
import time
import subprocess
import os
import re
from datetime import datetime

REPORT_DIR = "/home/csgoserver/cs2_crash_reports"
LAST_CRASH_FILE = "/home/csgoserver/LAST_CRASH.txt"
os.makedirs(REPORT_DIR, exist_ok=True)

def get_cs2_pid():
    try:
        out = subprocess.check_output(["pidof", "cs2"]).decode().strip()
        pids = out.split()
        return int(pids[0]) if pids else None
    except Exception:
        return None

def check_recent_journal_crash():
    try:
        out = subprocess.check_output([
            "journalctl", "-u", "cs2", "--since", "1 minute ago", "--no-pager"
        ]).decode("utf-8", errors="replace")
        for line in out.splitlines():
            if any(term in line for term in ["WatchDog!", "FATAL ERROR", "core-dump", "status=11/SEGV", "killed", "Segmentation fault"]):
                return out, line
    except Exception:
        pass
    return None, None

def save_crash_report(reason, journal_snippet):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = os.path.join(REPORT_DIR, f"crash_{timestamp}.log")
    
    # Grab last 150 lines of journalctl
    try:
        journal_full = subprocess.check_output([
            "journalctl", "-u", "cs2", "--no-pager", "-n", "150"
        ]).decode("utf-8", errors="replace")
    except Exception as e:
        journal_full = f"Failed to get journal: {e}"

    # Grab last 100 lines of latest CSS log
    css_log = "None"
    try:
        log_dir = "/home/csgoserver/server-cs2/game/csgo/addons/counterstrikesharp/logs"
        if os.path.isdir(log_dir):
            files = sorted([os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.startswith("log-all")], key=os.path.getmtime)
            if files:
                with open(files[-1], "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    css_log = "".join(lines[-100:])
    except Exception as e:
        css_log = f"Failed to get CSS log: {e}"

    report_content = f"""================================================================================
CS2 SERVER CRASH DETECTED AT {timestamp} UTC
REASON: {reason}
================================================================================

=== TRIGGER SNIPPET ===
{journal_snippet}

=== JOURNALCTL (LAST 150 LINES) ===
{journal_full}

=== COUNTERSTRIKESHARP LOG (LAST 100 LINES) ===
{css_log}
================================================================================
"""
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    summary_line = f"[{timestamp} UTC] CRASH: {reason} | Report: {report_file}\n"
    with open(LAST_CRASH_FILE, "a", encoding="utf-8") as f:
        f.write(summary_line)
    
    print(summary_line)

def main():
    print("[CrashMonitor] Started CS2 crash monitoring daemon...")
    last_pid = get_cs2_pid()
    last_reported_time = 0

    while True:
        time.sleep(2)
        current_pid = get_cs2_pid()

        # If PID changed or process vanished, check journal
        if current_pid != last_pid and last_pid is not None:
            now = time.time()
            if now - last_reported_time > 10:
                journal_out, trigger_line = check_recent_journal_crash()
                if trigger_line:
                    save_crash_report(f"Process PID {last_pid} exited (trigger: {trigger_line})", journal_out)
                    last_reported_time = now
                elif current_pid is None:
                    save_crash_report(f"Process PID {last_pid} terminated unexpectedly", "Process disappeared from pidof")
                    last_reported_time = now

        last_pid = current_pid

if __name__ == "__main__":
    main()
