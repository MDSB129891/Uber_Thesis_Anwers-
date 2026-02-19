#!/usr/bin/env bash
set -euo pipefail

TICKER="${1:-}"
if [[ -z "$TICKER" ]]; then
  echo "Usage: ./scripts/open_pack.sh TICKER"
  exit 1
fi

# Normalize
TICKER_UPPER="$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')"

DASH="outputs/decision_dashboard_${TICKER_UPPER}.html"
CLICK="outputs/news_clickpack_${TICKER_UPPER}.html"
CLAIMS="outputs/claim_evidence_${TICKER_UPPER}.html"
PDF="export/${TICKER_UPPER}_Full_Investment_Memo.pdf"
DOCX="export/${TICKER_UPPER}_Full_Investment_Memo.docx"
MD="outputs/${TICKER_UPPER}_Full_Investment_Memo.md"
METH_MD="outputs/${TICKER_UPPER}_Calculation_Methodology.md"
ALERTS="outputs/alerts_${TICKER_UPPER}.json"
VERACITY="outputs/veracity_${TICKER_UPPER}.json"
METH_DOCX="export/${TICKER_UPPER}_Calculation_Methodology.docx"

echo ""
echo "🚀 OPEN PACK (all eggs on screen)"
echo "Ticker: ${TICKER_UPPER}"
echo ""

# Always try to open the ONE master screen first
if [[ -f "$DASH" ]]; then
  echo "🧠 Opening dashboard: $DASH"
  open "$DASH"
else
  echo "⚠️ Missing dashboard: $DASH"
fi

# Then open the rest (best-effort)
for f in "$PDF" "$CLICK" "$CLAIMS" "$MD" "$DOCX" "$METH_MD" "$METH_DOCX" "$ALERTS" "$VERACITY"; do
  if [[ -f "$f" ]]; then
    echo "📌 Opening: $f"
    open "$f" || true
  else
    echo "… skip (missing): $f"
  fi
done

echo ""
echo "✅ Done. If something didn’t open, it’s listed as missing above."
