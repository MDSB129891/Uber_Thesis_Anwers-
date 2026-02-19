#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./scripts/galactus.sh "GM | I think they are going to increase EV production making their stock rise"
#
# Optional:
# PEERS="F,TM" ./scripts/galactus.sh "GM | thesis..."

INPUT="${1:-}"
if [[ -z "$INPUT" ]]; then
  echo "Usage: ./scripts/galactus.sh \"TICKER | thesis text\""
  exit 1
fi

TICKER="$(echo "$INPUT" | cut -d'|' -f1 | xargs)"
THESIS="$(echo "$INPUT" | cut -d'|' -f2- | xargs)"

if [[ -z "$TICKER" || -z "$THESIS" ]]; then
  echo "ERROR: format must be: TICKER | thesis"
  exit 1
fi

PEERS_ARG=""
if [[ -n "${PEERS:-}" ]]; then
  PEERS_ARG="--peers ${PEERS}"
fi

python3 scripts/galactus.py --ticker "$TICKER" --thesis "$THESIS" $PEERS_ARG
