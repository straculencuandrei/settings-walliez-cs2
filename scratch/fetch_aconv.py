import urllib.request, re

req = urllib.request.Request("https://online-audio-converter.com/static/js/aconv.js?895303", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
js = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

print("aconv.js size:", len(js))
with open("scratch/aconv.js", "w", encoding="utf-8") as f:
    f.write(js)

# Search for conversion parameters, ffmpeg, 44100, upload, api
matches = re.findall(r'(\w*(?:convert|upload|encoder|sample_rate|samplerate|44100|mp3|format|bitrate|quality)\w*)', js, re.IGNORECASE)
print("Found keywords:", set(matches[:40]))
