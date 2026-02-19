from pathlib import Path
import re

p = Path("scripts/build_thesis_memo.py")
txt = p.read_text(encoding="utf-8")

# Replace hardcoded thesis loader
txt = re.sub(
    r'thesis\s*=\s*json\.load\(open\(THESES\s*/\s*f"\{ticker\}_thesis\.json"\)\)',
    'thesis = json.load(open(args.thesis))',
    txt
)

p.write_text(txt, encoding="utf-8")
print("DONE ✅ build_thesis_memo now uses --thesis path")
