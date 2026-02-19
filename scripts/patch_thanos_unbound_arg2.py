from __future__ import annotations
from pathlib import Path
import re

p = Path("scripts/run_thanos.sh")
src = p.read_text(encoding="utf-8")

# If it already uses ${2:-...} we're done.
if re.search(r"\$\{2:-", src):
    print("OK ✅ arg2 already optional")
    raise SystemExit(0)

lines = src.splitlines(True)
out = []
patched = 0

for line in lines:
    # Convert any plain $2 usage to ${2:-}
    # but only for simple assignments or echo prints referencing thesis override
    if "$2" in line and "${2" not in line:
        # safest: replace standalone $2 tokens with ${2:-}
        # (won’t touch $20 etc — rare in bash scripts)
        newline = re.sub(r"(?<!\d)\$2\b", r"${2:-}", line)
        if newline != line:
            patched += 1
        out.append(newline)
    else:
        out.append(line)

p.write_text("".join(out), encoding="utf-8")
print(f"OK ✅ patched run_thanos.sh (made $2 optional in {patched} place(s))")
