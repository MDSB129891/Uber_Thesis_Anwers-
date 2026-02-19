from pathlib import Path

p = Path("scripts/build_investment_memo.py")
lines = p.read_text(encoding="utf-8").splitlines()

out = []
skip = False

for ln in lines:
    # Kill the Stormbreaker markdown injection area
    if "Stormbreaker" in ln or "_render_claim_evidence_md" in ln:
        skip = True
        continue

    # Stop skipping once we hit doc creation
    if skip and ln.lstrip().startswith("doc = Document"):
        skip = False

    if not skip:
        out.append(ln)

p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("NUKED broken Stormbreaker indent block")
