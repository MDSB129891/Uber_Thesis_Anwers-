#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "run_uber_update.py"

txt = TARGET.read_text(encoding="utf-8").splitlines(True)

# Find where top-of-file ends (before first def/class)
top_end = None
for i, line in enumerate(txt):
    if re.match(r"^\s*(def|class)\s+\w+", line):
        top_end = i
        break
if top_end is None:
    top_end = min(len(txt), 200)

top = txt[:top_end]
rest = txt[top_end:]

# 1) Remove the exact known offender line(s)
top = [ln for ln in top if not re.match(r"^\s*\+\s*PEERS\s*$", ln)]

# 2) Remove old/fragmented universe/peers/ticker blocks in the top section
drop_patterns = [
    r"^\s*TICKER\s*=\s*.*$",
    r"^\s*PEERS\s*=\s*.*$",
    r"^\s*UNIVERSE\s*=\s*.*$",
    r"^\s*UNIVERSE_ENV\s*=\s*.*$",
]
filtered = []
for ln in top:
    if any(re.match(p, ln) for p in drop_patterns):
        continue
    filtered.append(ln)
top = filtered

# 3) Ensure import os exists in top (after future import if present)
has_os = any(re.match(r"^\s*import\s+os\b", ln) for ln in top)
if not has_os:
    inserted = False
    for i, ln in enumerate(top):
        if re.match(r"^\s*from\s+__future__\s+import\s+annotations\s*$", ln):
            top.insert(i + 1, "\nimport os\n")
            inserted = True
            break
    if not inserted:
        top.insert(0, "import os\n")

# 4) Insert our clean, safe universe block near the top (after imports)
universe_block = (
    "\n"
    "# ---- Thanos-safe universe config (do not edit by hand) ----\n"
    "TICKER = os.getenv(\"TICKER\", \"UBER\").strip().upper()\n"
    "PEERS = [s.strip().upper() for s in os.getenv(\"PEERS\", \"LYFT,DASH\").split(\",\") if s.strip()]\n"
    "UNIVERSE = [TICKER] + [p for p in PEERS if p != TICKER]\n"
    "# Optional override: set UNIVERSE=\"UBER,LYFT,DASH\" to fully control\n"
    "UNIVERSE_ENV = os.getenv(\"UNIVERSE\", \"\")\n"
    "if UNIVERSE_ENV.strip():\n"
    "    UNIVERSE = [s.strip().upper() for s in UNIVERSE_ENV.split(\",\") if s.strip()]\n"
    "# -----------------------------------------------------------\n"
    "\n"
)

# Place block after the last import line in top
last_import_idx = -1
for i, ln in enumerate(top):
    if re.match(r"^\s*(from\s+\S+\s+import|import)\b", ln):
        last_import_idx = i

insert_at = last_import_idx + 1
top.insert(insert_at, universe_block)

new_txt = "".join(top + rest)
TARGET.write_text(new_txt, encoding="utf-8")

print("DONE ✅ Fixed scripts/run_uber_update.py (PEERS/UNIVERSE block repaired)")
