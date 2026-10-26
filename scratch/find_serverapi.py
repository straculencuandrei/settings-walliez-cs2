import urllib.request, re

for bundle in ["shared-v3-lib.js?e4221f", "shared-v3-app.js?5ca147"]:
    req = urllib.request.Request(f"https://online-audio-converter.com/static/js/{bundle}", headers={"User-Agent": "Mozilla/5.0"})
    js = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
    for m in re.finditer(r'ServerAPI\b', js):
        snippet = js[m.start()-20:m.start()+200]
        if any(w in snippet for w in [":{", "={", "function", "var "]):
            print(bundle, snippet)
