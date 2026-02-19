from pathlib import Path
import re

P = Path("scripts/build_super_memo.py")
txt = P.read_text()

# Remove EVERYTHING between Red flags and Thesis test (broken region)
txt = re.sub(
    r"(## 7\) Red flags[\\s\\S]*?)(## 8\))",
    r"\\1\n\\2",
    txt,
    flags=re.M
)

P.write_text(txt, encoding="utf-8")
print("🧨 Nuked broken story block safely.")
