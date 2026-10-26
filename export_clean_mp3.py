#!/usr/bin/env python3
"""
Clean 44.1kHz MP3 Audio Converter
Implements the exact encoding algorithm of https://onlineaudioconverter.com/ (123apps):
- Encoder: libmp3lame
- Sampling Rate: 44,100 Hz (44.1 kHz)
- Channels: Stereo (2 channels)
- Bitrate: 320 kbps CBR (Constant Bitrate)
- Metadata: Completely stripped (-map_metadata -1, clean ID3v2.3)
- Trimming: Optional 10.0s trim with smooth 1.0s fadeout (9.0s -> 10.0s)
"""

import os
import sys
import shutil
import subprocess

# Local ffmpeg search paths
FFMPEG_CANDIDATES = [
    r"C:\Users\buzunar\Documents\game\ytallinone\bin\ffmpeg.exe",
    shutil.which("ffmpeg") or ""
]

def find_ffmpeg():
    for path in FFMPEG_CANDIDATES:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError("ffmpeg.exe could not be found. Please ensure ffmpeg is available.")

def convert_to_clean_44k_mp3(input_file, output_file=None, start_time="0", duration=10, fadeout=True):
    """
    Converts any audio file to a clean 44.1kHz MP3 using the exact
    algorithm of onlineaudioconverter.com.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    ffmpeg = find_ffmpeg()

    if output_file is None:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}_clean_44k.mp3"

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    cmd = [ffmpeg, "-y"]

    # Start time offset
    if start_time and str(start_time).strip() not in ["0", "00:00", "0:00"]:
        cmd.extend(["-ss", str(start_time).strip()])

    cmd.extend(["-i", input_file])

    # Trimming and Fadeout
    if duration and duration > 0:
        cmd.extend(["-t", str(duration)])
        if fadeout and duration > 1:
            fade_start = duration - 1
            cmd.extend(["-af", f"afade=t=out:st={fade_start}:d=1"])

    # Exact onlineaudioconverter.com algorithm parameters:
    # 1. libmp3lame codec
    # 2. 44.1 kHz sample rate
    # 3. 2 channels (stereo)
    # 4. 320k Constant Bitrate (CBR)
    # 5. Stripped metadata (-map_metadata -1)
    # 6. ID3v2.3 standard tags
    cmd.extend([
        "-codec:a", "libmp3lame",
        "-b:a", "320k",
        "-ar", "44100",
        "-ac", "2",
        "-map_metadata", "-1",
        "-id3v2_version", "3",
        "-write_id3v1", "1",
        output_file
    ])

    print(f"[*] Converting: {os.path.basename(input_file)}")
    print(f"    Target: MP3 | 44.1 kHz | Stereo | 320 kbps CBR | Clean Metadata")
    if duration and duration > 0:
        print(f"    Trim: {duration}s (Start: {start_time}, 1s smooth fadeout)")

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] FFmpeg error:\n{res.stderr}")
        raise RuntimeError(f"FFmpeg conversion failed: {res.stderr}")

    out_size = os.path.getsize(output_file)
    print(f"[+] Output ready: {output_file} ({out_size:,} bytes)")
    return output_file

def convert_to_clean_44k_wav(input_file, output_file=None, start_time="0", duration=10, fadeout=True):
    """
    Also generates a clean 44.1kHz 16-bit PCM stereo WAV if needed by resourcecompiler.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    ffmpeg = find_ffmpeg()

    if output_file is None:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}_clean_44k.wav"

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    cmd = [ffmpeg, "-y"]

    if start_time and str(start_time).strip() not in ["0", "00:00", "0:00"]:
        cmd.extend(["-ss", str(start_time).strip()])

    cmd.extend(["-i", input_file])

    if duration and duration > 0:
        cmd.extend(["-t", str(duration)])
        if fadeout and duration > 1:
            fade_start = duration - 1
            cmd.extend(["-af", f"afade=t=out:st={fade_start}:d=1"])

    cmd.extend([
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-map_metadata", "-1",
        output_file
    ])

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg WAV conversion failed: {res.stderr}")

    return output_file

def batch_convert(paths, duration=10, output_dir=None):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for f in os.listdir(p):
                ext = os.path.splitext(f)[1].lower()
                if ext in [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"]:
                    files.append(os.path.join(p, f))
        elif os.path.isfile(p):
            files.append(p)

    if not files:
        print("[!] No audio files found to convert.")
        return []

    print(f"[*] Found {len(files)} file(s) for batch conversion.")
    results = []
    for f in files:
        base_name = os.path.splitext(os.path.basename(f))[0]
        out_name = f"{base_name}.mp3"
        if output_dir:
            out_path = os.path.join(output_dir, out_name)
        else:
            out_path = os.path.join(os.path.dirname(f), f"{base_name}_clean44k.mp3")

        try:
            res = convert_to_clean_44k_mp3(f, out_path, duration=duration)
            results.append(res)
        except Exception as ex:
            print(f"[!] Error converting {f}: {ex}")

    print(f"\n[+] Successfully converted {len(results)} of {len(files)} files!")
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_clean_mp3.py <file_or_dir1> [file_or_dir2...]")
        print("Or drag and drop files onto Convert_To_Clean_44k_MP3.bat")
        sys.exit(1)

    batch_convert(sys.argv[1:])
