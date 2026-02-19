from pathlib import Path
import re

p = Path("scripts/run_thanos.sh")
txt = p.read_text(encoding="utf-8")

# Force thesis default
txt = re.sub(
    r'THESIS_OVERRIDE=.*',
    'THESIS_OVERRIDE="${2:-}"\nTHESIS_PATH="${THESIS_OVERRIDE:-theses/${TICKER}_thesis_base.json}"',
    txt
)

# Replace build_claim_evidence call
txt = re.sub(
    r'python3 scripts/build_claim_evidence.py.*',
    'python3 scripts/build_claim_evidence.py --ticker "${TICKER}" --thesis "${THESIS_PATH}"',
    txt
)

p.write_text(txt, encoding="utf-8")
print("OK ✅ claim evidence now always uses thesis file")
