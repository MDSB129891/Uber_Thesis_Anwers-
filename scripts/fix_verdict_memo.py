#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("scripts/build_investment_memo.py")
txt = p.read_text(encoding="utf-8")

lines = txt.splitlines()

out = []
for ln in lines:
    # Drop the broken injected line if present
    if "verdict_sentence = build_verdict" in ln or "print(\"verdict_sentence" in ln:
        continue
    out.append(ln)

txt = "\n".join(out)

# Insert correct verdict block just before final memo write
needle = "print(\"DONE ✅ Memo created:\""

verdict_block = """
    # ---- Analyst-style verdict sentence ----
    try:
        from scripts.verdict import build_verdict
        verdict_sentence = build_verdict(decision_summary, proxy_row if 'proxy_row' in locals() else None)
    except Exception as _e:
        verdict_sentence = f"Verdict: {decision_summary.get('rating')} (score {decision_summary.get('score')}/100)."
    # ---------------------------------------
"""

if needle in txt:
    txt = txt.replace(needle, verdict_block + "\n" + needle)

p.write_text(txt, encoding="utf-8")
print("DONE ✅ build_investment_memo.py repaired")
