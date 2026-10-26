with open("scratch/aconv.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Look for ajax, fetch, post, socket, convert
for m in re.finditer(r'(convert|format|bitrate|sample_rate|samplerate|channels|encoder)', js, re.IGNORECASE):
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 100)
    snippet = js[start:end]
    if any(k in snippet.lower() for k in ["post", "ajax", "url", "param", "data:", "json", "endpoint"]):
        print("Snippet:", snippet.replace('\n', ' '))
        print("-" * 50)
