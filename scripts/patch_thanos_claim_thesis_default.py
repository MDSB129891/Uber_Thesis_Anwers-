from pathlib import Path
import re

p = Path("scripts/run_thanos.sh")
txt = p.read_text(encoding="utf-8")

lines = txt.splitlines(True)
out = []
inserted = False

for line in lines:
    if (not inserted) and re.search(r"^\s*THESIS_OVERRIDE\s*=", line):
        out.append(line)
        out.append('THESIS_PATH="${THESIS_OVERRIDE:-theses/${TICKER}_thesis_base.json}"\n')
        inserted = True
        continue
    out.append(line)

txt2 = "".join(out)

pattern = r"(python3\s+scripts/build_claim_evidence\.py\s+--ticker\s+\"\$\{?TICKER\}?\".*--thesis)(?:\s+\"?\$\{?THESIS_OVERRIDE\}?\"?)?"
def repl(m):
    return 'python3 scripts/build_claim_evidence.py --ticker "${TICKER}" --thesis "${THESIS_PATH}"'

txt3, n = re.subn(pattern, repl, txt2)

if n == 0:
    txt3 = re.sub(
        r"python3\s+scripts/build_claim_evidence\.py.*",
        'python3 scripts/build_claim_evidence.py --ticker "${TICKER}" --thesis "${THESIS_PATH}"',
        txt2,
        count=1
    )
    n = 1

p.write_text(txt3, encoding="utf-8")
print(f"OK patched run_thanos.sh")
