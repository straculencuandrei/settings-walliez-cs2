with open("scratch/aconv.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find("ServerAPI.")
while pos != -1:
    print(js[pos-50:pos+300])
    print("="*60)
    pos = js.find("ServerAPI.", pos+1)
