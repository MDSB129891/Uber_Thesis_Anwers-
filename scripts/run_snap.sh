#!/usr/bin/env bash
set -euo pipefail

CFG="config/run_config.json"
if [ ! -f "$CFG" ]; then
  echo "Missing $CFG"
  exit 1
fi

# Parse config (no jq)
TICKER=$(python3 - <<'PY'
import json
cfg=json.load(open("config/run_config.json"))
print(cfg["ticker"].strip().upper())
PY
)

PEERS=$(python3 - <<'PY'
import json
cfg=json.load(open("config/run_config.json"))
peers=cfg.get("peers") or []
print(",".join([str(p).strip().upper() for p in peers if str(p).strip()]))
PY
)

MODE=$(python3 - <<'PY'
import json
cfg=json.load(open("config/run_config.json"))
print((cfg.get("mode") or "hybrid").strip().lower())
PY
)

THESIS_FILE=$(python3 - <<'PY'
import json, os
cfg=json.load(open("config/run_config.json"))
t=cfg.get("thesis") or {}
ticker=cfg.get("ticker","").strip().upper()
variant=(t.get("variant") or "base").strip().lower()
explicit=t.get("file")
if explicit:
    print(str(explicit))
else:
    print(f"theses/{ticker}_thesis_{variant}.json")
PY
)

CLEANUP=$(python3 - <<'PY'
import json
cfg=json.load(open("config/run_config.json"))
sb=cfg.get("stormbreaker") or {}
print("1" if sb.get("enable_news_cleanup", True) else "0")
PY
)

CLAIM_EVIDENCE=$(python3 - <<'PY'
import json
cfg=json.load(open("config/run_config.json"))
sb=cfg.get("stormbreaker") or {}
print("1" if sb.get("enable_claim_evidence", True) else "0")
PY
)

echo "🦾 SNAP RUN"
echo "mode=$MODE"
echo "ticker=$TICKER"
echo "peers=$PEERS"
echo "thesis=$THESIS_FILE"

# Ensure thesis exists (generate suite if missing)
if [ ! -f "$THESIS_FILE" ]; then
  echo "Thesis file not found: $THESIS_FILE"
  echo "Generating thesis suite..."
  python3 scripts/generate_thesis_suite.py --ticker "$TICKER" >/dev/null 2>&1 || true
fi

# Run core Thanos (still the workhorse)
TICKER="$TICKER" PEERS="$PEERS" ./scripts/run_thanos.sh "$TICKER" "$THESIS_FILE"

# Stormbreaker: cleanup/upgrade evidence files (dedupe + whitelist boost)
if [ "$CLEANUP" = "1" ]; then
  python3 scripts/stormbreaker_news_cleanup.py --ticker "$TICKER"
fi

# Hybrid trust layer
python3 scripts/build_hybrid_signals.py --ticker "$TICKER" --mode "$MODE"
python3 scripts/build_ironman_appendix.py --ticker "$TICKER"

# Claim → Evidence mapping (makes theses verifiable without “manual hunting”)
if [ "$CLAIM_EVIDENCE" = "1" ]; then
  python3 scripts/build_claim_evidence.py --ticker "$TICKER" --thesis "$THESIS_FILE"
fi

echo "DONE ✅ SNAP PACK"
echo "- outputs/hybrid_signals_${TICKER}.json"
echo "- outputs/ironman_appendix_${TICKER}.md"
if [ "$CLEANUP" = "1" ]; then
  echo "- data/processed/news_unified_clean.csv"
fi
if [ "$CLAIM_EVIDENCE" = "1" ]; then
  echo "- outputs/claim_evidence_${TICKER}.json"
  echo "- outputs/claim_evidence_${TICKER}.html"
fi
