from pathlib import Path
import re

p = Path("scripts/run_thanos.sh")
txt = p.read_text()

fixed = []
for line in txt.splitlines():
    if "build_claim_evidence.py" in line:
        fixed.append('python3 scripts/build_claim_evidence.py --ticker "$TICKER" --thesis "theses/${TICKER}_thesis_base.json"')
    else:
        fixed.append(line)

p.write_text("\n".join(fixed) + "\n")

print("DONE ✅ claim evidence hardwired to default thesis")
