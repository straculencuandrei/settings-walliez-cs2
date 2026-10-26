with open("scratch/aconv.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find("duration_in_seconds:")
if pos != -1:
    print(js[pos-800:pos+300])
