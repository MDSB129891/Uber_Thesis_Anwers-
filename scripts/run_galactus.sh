#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_galactus.sh TICKER THESIS_JSON [PEERS_CSV]

TICKER="${1:-}"
THESIS_FILE="${2:-}"
PEERS_CSV="${3:-}"

if [[ -z "${TICKER}" || -z "${THESIS_FILE}" ]]; then
  echo "❌ Usage: ./scripts/run_galactus.sh TICKER THESIS_JSON [PEERS_CSV]"
  exit 1
fi

if [[ ! -f "${THESIS_FILE}" ]]; then
  echo "❌ Thesis file not found: ${THESIS_FILE}"
  echo "Tip: generate it with:"
  echo "  python3 scripts/new_thesis.py ${TICKER} \"your thesis text\""
  exit 1
fi

# Uppercase safely without bash-specific ${VAR^^}
TICKER_UC="$(printf "%s" "${TICKER}" | tr '[:lower:]' '[:upper:]')"

# Default peers if user didn't pass them
# IMPORTANT: these are literals, not variables like $DASH
if [[ -z "${PEERS_CSV}" ]]; then
  case "${TICKER_UC}" in
    UBER|LYFT|DASH)
      PEERS_CSV="LYFT,DASH"
      ;;
    TSLA)
      PEERS_CSV="GM,F"
      ;;
    GM)
      PEERS_CSV="F,TM"
      ;;
    F)
      PEERS_CSV="GM,TM"
      ;;
    *)
      PEERS_CSV="SPY"
      ;;
  esac
fi

echo "🌌 GALACTUS RUN"
echo "Ticker: ${TICKER_UC}"
echo "Thesis file: ${THESIS_FILE}"
echo "Peers: ${PEERS_CSV}"
echo

export PEERS="${PEERS_CSV}"

./scripts/run_thanos.sh "${TICKER_UC}" "${THESIS_FILE}"

echo
echo "🚀 OPENING RESULTS (dopamine mode)"
open "outputs/decision_dashboard_${TICKER_UC}.html" 2>/dev/null || true
open "outputs/news_clickpack_${TICKER_UC}.html" 2>/dev/null || true
open "export/${TICKER_UC}_Full_Investment_Memo.pdf" 2>/dev/null || true
open "export/${TICKER_UC}_Full_Investment_Memo.docx" 2>/dev/null || true

echo
echo "🧠 GALACTUS COMPLETE"
