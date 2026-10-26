import urllib.request, re, json

req = urllib.request.Request("https://online-audio-converter.com/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Find JS bundles
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print("Scripts found:")
for s in scripts:
    print(" ", s)

# Find config in html
glob_match = re.search(r'window\.glob\s*=\s*({.*?});', html)
if glob_match:
    glob_data = json.loads(glob_match.group(1))
    print("Encoder Host:", glob_data.get("encoder_host"))
    print("Files Host:", glob_data.get("files_host"))
    print("App ID:", glob_data.get("app_id"))
