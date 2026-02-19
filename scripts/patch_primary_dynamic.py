#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "run_uber_update.py"

txt = TARGET.read_text(encoding="utf-8")

# We expect our earlier universe config block exists now, so TICKER + UNIVERSE should be defined.
# Fix PRIMARY if it exists and is hardcoded.
changed = False

# Case A: PRIMARY = "UBER"
pattern_a = r'^\s*PRIMARY\s*=\s*["\']UBER["\']\s*$'
if re.search(pattern_a, txt, flags=re.M):
    txt = re.sub(pattern_a, 'PRIMARY = UNIVERSE[0]  # dynamic primary ticker', txt, flags=re.M)
    changed = True

# Case B: PRIMARY = TICKER or something else but hardcoded string
pattern_b = r'^\s*PRIMARY\s*=\s*["\'][A-Z]{1,6}["\']\s*$'
if re.search(pattern_b, txt, flags=re.M):
    txt = re.sub(pattern_b, 'PRIMARY = UNIVERSE[0]  # dynamic primary ticker', txt, flags=re.M)
    changed = True

# If no PRIMARY variable exists, add one right after UNIVERSE is defined.
if "PRIMARY" not in txt:
    # Insert after the "UNIVERSE =" line from our Thanos-safe block
    # Find the first occurrence of "UNIVERSE =" assignment line
    m = re.search(r'^(UNIVERSE\s*=\s*\[TICKER\].*)$', txt, flags=re.M)
    if m:
        insert_pos = m.end()
        txt = txt[:insert_pos] + "\nPRIMARY = UNIVERSE[0]  # dynamic primary ticker\n" + txt[insert_pos:]
        changed = True

# Also ensure any error message referencing PRIMARY is okay (no change needed)
TARGET.write_text(txt, encoding="utf-8")

print("DONE ✅ Patched PRIMARY to be dynamic (PRIMARY = UNIVERSE[0])" if changed else "No PRIMARY patch needed ✅")
