import urllib.request, urllib.error

url = "https://s85.online-audio-converter.com/aconv/upload/flow/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    resp = urllib.request.urlopen(req)
    print("Status:", resp.status)
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode('utf-8', errors='ignore')[:300])
except Exception as e:
    print("Error:", e)
