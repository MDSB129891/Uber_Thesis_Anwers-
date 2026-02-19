# Calculation Methodology — GM
*Generated: 2026-02-19 04:07 UTC*

## Purpose
This document explains how the engine calculates metrics, bucket scores, and the final rating.
Implementation reference: `scripts/run_uber_update.py`.

## Data Inputs
- `data/processed/fundamentals_annual_history.csv`
- `data/processed/comps_snapshot.csv`
- `data/processed/news_sentiment_proxy.csv`
- `data/processed/news_risk_dashboard.csv`
- `outputs/decision_summary.json` or `outputs/decision_summary_<T>.json`

## Derived Metric Formulas
- `capex_spend = abs(capitalExpenditure)`
- `free_cash_flow = operating_cash_flow - capex_spend`
- `revenue_ttm = rolling_4q_sum(revenue)`
- `fcf_ttm = rolling_4q_sum(free_cash_flow)`
- `fcf_margin_ttm_pct = (fcf_ttm / revenue_ttm) * 100`
- `revenue_ttm_yoy_pct = pct_change_4q(revenue_ttm) * 100`
- `fcf_ttm_yoy_pct = pct_change_4q(fcf_ttm) * 100`
- `net_debt = debt - cash`
- `fcf_yield = fcf_ttm / market_cap`
- `net_debt_to_fcf_ttm = net_debt / fcf_ttm` (only if `fcf_ttm > 0`)
- `rank_percentile(metric) = mean(peer_values <= company_value) * 100`

## Score Construction (0-100)
- `score = clamp(cash_level + valuation + growth + quality + balance_risk, 0, 100)`
- Rating bands: `BUY` if score >= 80, `HOLD` if score >= 65, else `AVOID`.

### Bucket Rules
- Cash Level (max 25): thresholded by `fcf_ttm` (>=12B, >=8B, >=4B, >=1B, else low).
- Valuation (max 20): absolute `fcf_yield` points + relative peer-rank points.
- Growth (max 20): revenue YoY leg + FCF YoY leg + two peer-rank legs.
- Quality (max 15): FCF margin leg + peer-rank leg.
- Balance/Risk (max 20): starts at 20 then subtracts debt/news/shock/core-risk penalties, with proxy-score adjustment.

## Worked Example (Current Run)
- Model score/rating: **52 / AVOID**
- Reconstructed score from current inputs: **52**

### Inputs Used
- FCF TTM: $11.07B
- FCF Yield: 14.19%
- Revenue YoY: -1.29%
- FCF YoY: -285.18%
- FCF Margin TTM: 5.99%
- Net Debt / FCF: 9.87
- Peer rank (FCF Yield): 66.67%
- Peer rank (Revenue YoY): 33.33%
- Peer rank (FCF YoY): 33.33%
- Peer rank (FCF Margin): 33.33%
- News neg 7d: 0
- News shock 7d: 0
- Core risk hits 30d (LABOR+INSURANCE+REGULATORY): 7
- Proxy score 7d: 68.00

### Bucket Contributions (Reconstructed)
- Cash Level: **21** | FCF TTM >= 8B
- Valuation: **17** | absolute leg: +10 (fcf_yield >= 8%); relative leg: +7 (rank >= 50)
- Growth: **0** | rev_yoy: -3; fcf_yoy: -5; rev rank leg applied; fcf rank leg applied
- Quality: **6** | margin leg: +3; rank leg applied
- Balance/Risk: **8** | start at 20; -8 debt penalty (nd_fcf >= 3.0); -4 core-risk frequency penalty (>= 6)

### Bucket Contributions (From Engine Output)
- cash_level: **21**
- valuation: **17**
- growth: **0**
- quality: **6**
- balance_risk: **8**

## Notes
- If reconstructed score and model score differ, the run may have mixed ticker-scoped vs shared summary files.
- This document is generated from current output files and mirrors current scoring logic.

