import urllib.request, re

req = urllib.request.Request("https://online-audio-converter.com/static/js/shared-v3-app.js?5ca147", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
js = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

print("shared-v3-app.js size:", len(js))
pos = js.find("ServerAPI=")
if pos == -1:
    pos = js.find("ServerAPI =")
if pos != -1:
    print(js[pos:pos+1500])
else:
    # search ServerAPI
    for m in re.finditer(r'ServerAPI\s*=', js):
        print(js[m.start():m.start()+1000])
