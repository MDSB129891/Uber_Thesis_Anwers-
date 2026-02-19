from __future__ import annotations
from pathlib import Path
import re

p = Path("scripts/run_thanos.sh")
src = p.read_text(encoding="utf-8").splitlines(True)

# 1) Insert THESIS_OVERRIDE="${2:-}" near the top (after TICKER is set, or after arg parsing)
inserted = False
out = []
for line in src:
    out.append(line)

    # Common patterns for ticker assignment
    if (not inserted) and re.search(r'^\s*TICKER=', line):
        out.append('THESIS_OVERRIDE="${2:-}"\n')
        inserted = True

# Fallback: insert after shebang if no TICKER= found
if not inserted:
    out = []
    for i, line in enumerate(src):
        out.append(line)
        if i == 0 and line.startswith("#!"):
            out.append('THESIS_OVERRIDE="${2:-}"\n')
            inserted = True

# 2) Replace any raw $2 references with $THESIS_OVERRIDE (safe with set -u)
fixed = []
replaced = 0
for line in out:
    if "$2" in line:
        # Replace standalone $2 and also occurrences like "$2", ${2}, etc.
        # Keep ${2:-} as-is (already safe)
        if "${2:-" in line:
            fixed.append(line)
            continue
        new = line
        new = new.replace("${2}", "${THESIS_OVERRIDE}")
        # Replace $2 token (best-effort)
        new = re.sub(r'(?<!\d)\$2\b', r'${THESIS_OVERRIDE}', new)
        if new != line:
            replaced += 1
        fixed.append(new)
    else:
        fixed.append(line)

p.write_text("".join(fixed), encoding="utf-8")
print(f"OK ✅ hardfixed run_thanos.sh: inserted THESIS_OVERRIDE and replaced $2 in {replaced} line(s)")
