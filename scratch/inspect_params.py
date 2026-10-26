with open("scratch/aconv.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Find ServerAPI or convert call
pos = js.find("ServerAPI.")
if pos != -1:
    print(js[pos-200:pos+500])

pos2 = js.find("advancedSettingPanel")
if pos2 != -1:
    print("\n--- Advanced Settings ---")
    print(js[pos2-100:pos2+1000])
