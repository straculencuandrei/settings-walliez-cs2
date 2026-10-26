with open("scratch/Custom_MVP_Sounds_WASD.cs", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    stripped = line.strip()
    if any(stripped.startswith(k) for k in ["for (", "for(", "while (", "while(", "do {", "do{"]) or "while" in stripped or "for (" in stripped:
        print(f"Line {i+1}: {stripped}")
        for j in range(max(0, i-2), min(len(lines), i+15)):
            print(f"  {j+1}: {lines[j].rstrip()}")
        print("-" * 50)
