with open("scratch/aconv.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find("set_params")
while pos != -1:
    print(js[pos-100:pos+400])
    print("="*60)
    pos = js.find("set_params", pos+1)
