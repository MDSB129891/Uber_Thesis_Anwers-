#!/usr/bin/env bash
set -euo pipefail

T="${1:-}"
THESIS="${2:-}"

if [[ -z "$T" ]]; then
  echo "usage: $0 TICKER [thesis_json]"
  exit 1
fi

if [[ -z "$THESIS" ]]; then
  THESIS="theses/${T}_thesis_custom.json"
  [[ -f "$THESIS" ]] || THESIS="theses/${T}_thesis_base.json"
fi

echo "🪓 STORMBREAKER HULKBUSTER: $T"
echo "   thesis: $THESIS"

python3 scripts/stormbreaker_news_cleanup.py --ticker "$T" >/dev/null

python3 scripts/build_claim_evidence.py --ticker "$T" --thesis "$THESIS"

mkdir -p "export/CANON_${T}"
cp -f "outputs/claim_evidence_${T}.html" "export/CANON_${T}/claim_evidence_${T}.html"
cp -f "outputs/claim_evidence_${T}.json" "export/CANON_${T}/claim_evidence_${T}.json"

python3 - <<PY
import json
p=f"export/CANON_{'$T'}/claim_evidence_{'$T'}.json"
d=json.load(open(p))
res=d.get("results",[])
unknown=sum(1 for r in res if r.get("status")=="UNKNOWN")
fail=sum(1 for r in res if r.get("status")=="FAIL")
print(f"✅ claims: {len(res)} | PASS: {len(res)-unknown-fail} | FAIL: {fail} | UNKNOWN: {unknown}")
PY

echo "DONE ✅ export/CANON_${T}/claim_evidence_${T}.html"
echo "DONE ✅ export/CANON_${T}/claim_evidence_${T}.json"
