from __future__ import annotations
from pathlib import Path

SH = Path("scripts/run_thanos.sh")
if not SH.exists():
    raise SystemExit("ERROR: scripts/run_thanos.sh not found")

src = SH.read_text(encoding="utf-8")

marker = "=== 1) Engine update (financials + news) ==="
if marker not in src:
    raise SystemExit("ERROR: couldn't find engine step marker in run_thanos.sh")

sync_block = r'''
# --- GALACTUS: force shared summary to match this ticker (prevents ticker mismatch) ---
if [ -f "outputs/decision_summary_${TICKER}.json" ]; then
  cp "outputs/decision_summary_${TICKER}.json" "outputs/decision_summary.json"
fi
if [ -f "outputs/decision_explanation_${TICKER}.json" ]; then
  cp "outputs/decision_explanation_${TICKER}.json" "outputs/decision_explanation.json"
fi
'''.strip("\n")

if "GALACTUS: force shared summary" in src:
    print("OK ✅ sync block already present in run_thanos.sh")
    raise SystemExit(0)

# Insert right after the engine update python call
lines = src.splitlines(True)

out = []
inserted = False
for i, line in enumerate(lines):
    out.append(line)

    # Common engine call line patterns
    if ("python3 scripts/run_uber_update.py" in line) or ("python3 ./scripts/run_uber_update.py" in line) or ("scripts/run_uber_update.py" in line and "python" in line):
        # Insert sync block after engine run
        out.append("\n" + sync_block + "\n\n")
        inserted = True

if not inserted:
    # fallback: insert after marker line
    out = []
    for line in lines:
        out.append(line)
        if marker in line and not inserted:
            out.append("\n" + sync_block + "\n\n")
            inserted = True

if not inserted:
    raise SystemExit("ERROR: couldn't find where to insert sync block")

SH.write_text("".join(out), encoding="utf-8")
print("OK ✅ patched run_thanos.sh to sync decision_summary.json to the current ticker")
