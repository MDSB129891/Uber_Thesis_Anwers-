from pathlib import Path

p = Path("scripts/run_thanos.sh")
txt = p.read_text()

lines = txt.splitlines()
out = []

for line in lines:
    if line.strip().startswith("THESIS_OVERRIDE="):
        out.append('THESIS_PATH="${2:-theses/${TICKER}_thesis_base.json}"')
    elif "build_claim_evidence.py" in line:
        out.append('python3 scripts/build_claim_evidence.py --ticker "$TICKER" --thesis "$THESIS_PATH"')
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n")

print("DONE ✅ Stormbreaker final patch applied")
