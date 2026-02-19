#!/usr/bin/env bash
set -euo pipefail

TICKER="${1:-}"
THESIS="${2:-}"

if [[ -z "${TICKER}" || -z "${THESIS}" ]]; then
  echo "Usage: ./scripts/run_super.sh <TICKER> <THESIS_JSON_PATH>"
  exit 1
fi

# Uppercase ticker safely (works in bash 3.2 too)
TICKER_UPPER="$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')"

echo "🧠 SUPER RUN"
echo "Ticker: $TICKER_UPPER"
echo "Thesis: $THESIS"
echo

# 1) Build SUPER memo (md + docx)
python3 scripts/build_super_memo.py --ticker "$TICKER_UPPER" --thesis "$THESIS"

# 2) Convert DOCX -> PDF using LibreOffice (soffice)
SOFFICE_BIN="$(command -v soffice || true)"
if [[ -z "$SOFFICE_BIN" ]]; then
  echo "❌ soffice not found. You already have it at /opt/homebrew/bin/soffice though."
  exit 1
fi

DOCX="export/${TICKER_UPPER}_SUPER_Memo.docx"
PDF="export/${TICKER_UPPER}_SUPER_Memo.pdf"

"$SOFFICE_BIN" --headless --convert-to pdf --outdir export "$DOCX" >/dev/null 2>&1 || true

# 3) OPEN IN ORDER (minimal dopamine, no spam)
DASH="outputs/decision_dashboard_${TICKER_UPPER}.html"
if [[ -f "$DASH" ]]; then open "$DASH" || true; fi
if [[ -f "$PDF" ]]; then open "$PDF" || true; fi

echo
echo "✅ DONE"
echo "- $DASH"
echo "- $PDF"
