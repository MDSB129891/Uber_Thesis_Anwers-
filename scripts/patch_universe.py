#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "run_uber_update.py"

txt = TARGET.read_text(encoding="utf-8")

# If already patched, exit cleanly
if "UNIVERSE_ENV" in txt and "os.getenv(\"UNIVERSE\"" in txt:
    print("Already patched ✅")
    raise SystemExit(0)

# Ensure os imported
if not re.search(r"^import os\b", txt, flags=re.M):
    # add after future import or at top
    if re.search(r"^from __future__ import annotations\s*$", txt, flags=re.M):
        txt = re.sub(r"(^from __future__ import annotations\s*$)", r"\1\n\nimport os", txt, flags=re.M)
    else:
        txt = "import os\n" + txt

# Replace common hardcoded universe patterns if found; otherwise insert a safe block
patterns = [
    r"UNIVERSE\s*=\s*\[[^\]]+\]",
    r"UNIVERSE\s*=\s*\([^\)]+\)",
    r"Universe:\s*\[[^\]]+\]",  # in print lines (harmless)
]

replacement_block = (
    "UNIVERSE_ENV = os.getenv(\"UNIVERSE\", \"UBER,LYFT,DASH\")\n"
    "UNIVERSE = [s.strip().upper() for s in UNIVERSE_ENV.split(\",\") if s.strip()]\n"
)

if re.search(patterns[0], txt):
    txt = re.sub(patterns[0], replacement_block, txt, flags=re.M)
elif re.search(patterns[1], txt):
    txt = re.sub(patterns[1], replacement_block, txt, flags=re.M)
else:
    # Insert near top after imports
    m = re.search(r"(import\s+[^\n]+\n)+", txt)
    if m:
        insert_at = m.end()
        txt = txt[:insert_at] + "\n" + replacement_block + "\n" + txt[insert_at:]
    else:
        txt = replacement_block + "\n" + txt

TARGET.write_text(txt, encoding="utf-8")
print("Patched run_uber_update.py ✅ (UNIVERSE env support added)")
