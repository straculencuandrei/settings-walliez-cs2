with open(r"C:\Users\buzunar\.gemini\antigravity-ide\brain\fcfbab7e-5aa1-4945-a84f-f8c3888faae9\scratch\GoldKingZ_original.cs", "r", encoding="utf-8") as f:
    code = f.read()

pos = code.find("for (int i = 1; i <= soundPathCou")
print(code[pos:pos+1500])
