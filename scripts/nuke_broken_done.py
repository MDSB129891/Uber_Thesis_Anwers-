from pathlib import Path
import re

p = Path("scripts/build_investment_memo.py")
txt = p.read_text(encoding="utf-8")

lines = txt.splitlines()

clean = []
removed = 0

for ln in lines:
    if "Memo created" in ln or "DONE" in ln:
        removed += 1
        continue
    clean.append(ln)

txt = "\n".join(clean)

# Add a safe print at the very end of main()
if "def main" in txt:
    txt += '\n\nprint("DONE Memo created")\n'

p.write_text(txt, encoding="utf-8")

print(f"Removed {removed} broken DONE lines and repaired file ✅")
