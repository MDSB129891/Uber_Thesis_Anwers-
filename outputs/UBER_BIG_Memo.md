# BIG Investment Memo — UBER
*Generated: 2026-02-19 02:30 UTC*

## What this is
This is a **novice-friendly** investment memo that explains:
- What the model concluded (score + rating)
- What data it used (financials + valuation + risk/news)
- Why it thinks that (claim evidence + click-to-verify sources)
- What would change the conclusion (alerts / red lines)

## Quick summary (read this first)
- Model rating: **AVOID** (score **52/100**)
- Confidence / veracity: **52/100**
- Bucket scores: `{'cash_level': 21, 'valuation': 17, 'growth': 0, 'quality': 6, 'balance_risk': 8}`

**High-level gut check (plain English):**
- **Score** is “business strength minus risk.” Higher = better.
- **Confidence** is “how easy it is to verify the evidence.” Higher = more reliable.

## Thesis being tested
- Thesis file: `theses/UBER_thesis_base.json`
If you supplied a thesis, we test its claims. If you did not, we use the auto base/bull/bear thesis pack.

## Core numbers (so humans can sanity-check)
- Revenue growth (YoY): **N/A**
- Free cash flow (latest): **N/A**
- FCF margin: **N/A**
- FCF yield (valuation vs cash): **N/A**

**How to interpret these (super plain English):**
- **Revenue growth**: is demand expanding, flat, or shrinking?
- **Free cash flow**: after paying bills + investments, is there cash left over?
- **FCF margin**: how much cash is created per $100 of sales.
- **FCF yield**: how much cash you get vs the price you pay for the stock (higher is usually “cheaper”).

## Red lines (what could break the story)
- No red lines found (or alerts file missing).

## What to open (dopamine mode)
- Dashboard: `outputs/decision_dashboard_UBER.html`
- News click-pack: `outputs/news_clickpack_UBER.html`
- Claim evidence (HTML): `outputs/claim_evidence_UBER.html`
- Veracity: `outputs/veracity_UBER.json`

## Thesis validation (PASS/FAIL)
# Thesis Validation Memo — UBER
*Generated: 2026-02-18 22:57 UTC*

## Thesis being tested
**UBER: Cash generation + reasonable valuation outweighs headline risk**
Uber can keep growing while converting revenue into free cash flow, and the stock is not overpriced versus that cash. Risks (insurance/regulatory/labor) are real but not escalating.

## Result
- Model rating: **BUY** (score 83/100)
- Thesis support: **100.0%**

## Claims checklist

- **PASS** — Revenue is still growing at a healthy pace  
  Metric `latest_revenue_yoy_pct` → **18.27959434262585**
- **PASS** — Free cash flow is positive  
  Metric `latest_free_cash_flow` → **9763000000.0**
- **PASS** — Free cash flow margin is solid  
  Metric `latest_fcf_margin_pct` → **18.768864025222523**
- **PASS** — Recent news shock is not severe (not a headline crisis)  
  Metric `news_shock_30d` → **-12**
- **PASS** — Valuation is not expensive versus cash (FCF yield is decent)  
  Metric `fcf_yield_pct` → **6.45153246939015**
- **PASS** — Insurance risk is not spiking recently  
  Metric `risk_insurance_neg_30d` → **2**

## Claim Evidence (Stormbreaker) — why the model believes what it believes
This section tries to attach **real articles** to each claim (bull vs bear).
If a claim is a **metric** (revenue growth, FCF margin), it may have fewer direct articles — that’s normal.

### PASS — Revenue is still growing at a healthy pace
- Metric: `latest_revenue_yoy_pct` | Actual: **18.27959434262585**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### PASS — Free cash flow is positive (business generates real cash)
- Metric: `latest_free_cash_flow` | Actual: **9763000000.0**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### PASS — Free cash flow margin is solid (company converts sales into cash)
- Metric: `latest_fcf_margin_pct` | Actual: **18.768864025222523**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### UNKNOWN — Valuation is not expensive versus cash (FCF yield is decent)
- Metric: `fcf_yield_pct` | Actual: **None**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### PASS — Recent news shock is not severe (not a headline crisis)
- Metric: `news_shock_30d` | Actual: **-12**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### PASS — Insurance risk is not spiking recently
- Metric: `risk_insurance_neg_30d` | Actual: **2**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### PASS — Regulatory risk is not spiking recently
- Metric: `risk_regulatory_neg_30d` | Actual: **1**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### UNKNOWN — Labor risk is not spiking recently
- Metric: `risk_labor_neg_30d` | Actual: **None**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).

### UNKNOWN — Debt burden is manageable (net debt <= ~3.0 years of free cash flow)
- Metric: `latest_net_debt_to_fcf` | Actual: **None**
**Bull evidence (support):**
- No matching bull articles found (normal for pure metric claims).
**Bear evidence (risk):**
- No matching bear articles found (normal for pure metric claims).


## Plain-English encyclopedia (Iron Man Appendix)
Appendix not found. Expected: outputs/ironman_appendix_<T>.md

