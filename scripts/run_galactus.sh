#!/usr/bin/env bash
set -e

FILE="inputs/galactus.txt"

if [ ! -f "$FILE" ]; then
  echo "Missing inputs/galactus.txt"
  exit 1
fi

source "$FILE"

if [ -z "$TICKER" ]; then
  echo "TICKER missing"
  exit 1
fi

echo "🌌 GALACTUS RUN"
echo "Ticker: $TICKER"
echo "Thesis: $THESIS"

# write thesis to json
cat > theses/${TICKER}_custom.json <<EOF
{
  "ticker": "$TICKER",
  "title": "Custom user thesis",
  "claims": [
    {
      "statement": "$THESIS",
      "metric": "latest_revenue_yoy_pct",
      "op": ">=",
      "threshold": 5
    }
  ]
}
EOF

chmod +x scripts/run_thanos.sh

./scripts/run_thanos.sh "$TICKER" theses/${TICKER}_custom.json
