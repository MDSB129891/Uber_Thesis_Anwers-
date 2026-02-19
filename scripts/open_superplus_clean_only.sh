#!/usr/bin/env bash
set -euo pipefail

T="${1:-}"
if [[ -z "$T" ]]; then
  echo "Usage: $0 <TICKER>"
  exit 1
fi

T_UP="$(echo "$T" | tr '[:lower:]' '[:upper:]')"

DASH="outputs/decision_dashboard_${T_UP}.html"
PDF="export/${T_UP}_SUPERPLUS_CLEAN_Memo.pdf"

echo "OPENING (only 2 things, in order):"
echo "1) $DASH"
echo "2) $PDF"
echo ""

if [[ -f "$DASH" ]]; then
  open "$DASH" || true
else
  echo "⚠️ Missing: $DASH"
fi

if [[ -f "$PDF" ]]; then
  open "$PDF" || true
else
  echo "⚠️ Missing: $PDF"
fi
