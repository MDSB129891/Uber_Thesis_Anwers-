# SUPER Investment Memo — GM
*Generated: 2026-02-19 04:23 UTC*

## 1) Your thesis (what you believe)
**GM: enterprise value (company value including debt) expansion drives margin recovery**
enterprise value (company value including debt) expansion drives margin recovery

## 2) What the model concluded (plain English)
- **Rating:** **AVOID** (score **52/100**)
- **Evidence confidence / veracity:** **46** (higher = more trustworthy coverage)

## 3) The 30-second explanation (for total beginners)
Think of this like a **car dashboard**:
- The **score** is the overall attractiveness estimate.
- The **buckets** explain *why* the score happened.
- The **news/risk** items try to spot headline landmines.
- The **thesis test** checks whether the facts match the story you’re betting on.

## 4) Core numbers (sanity-check)
- Revenue growth (compared to the same time last year): **-1.29%**  _(source: comps_snapshot → revenue_ttm_yoy_pct)_
- Free cash flow (over the last twelve months): **$11.07B**  _(source: comps_snapshot → fcf_ttm)_
- free cash flow (cash left after paying bills and investing in the business) margin: **5.99%**  _(source: comps_snapshot → fcf_margin_ttm_pct)_
- free cash flow (cash left after paying bills and investing in the business) yield: **14.19%**  _(source: comps_snapshot → fcf_yield_pct / fcf_yield)_

## 5) Balance sheet snapshot (why debt matters)
- Market cap: **$78.05B**
- Cash: **$20.95B**
- Debt: **$130.28B**
- net debt (total debt minus cash): **$109.33B**  _(debt minus cash)_
- net debt (total debt minus cash) / free cash flow (cash left after paying bills and investing in the business): **9.87x**  _(how many years of cash it takes to pay debt)_

## 6) Bucket scores (what drove the rating)
- **Cash strength** = **21** → Cash Level = does the business generate real cash and have liquidity?
- **Price vs value** = **17** → Valuation = are you paying a reasonable price vs the cash the business produces?
- **Growth** = **0** → Growth = are sales/cash expanding or shrinking?
- **Business quality** = **6** → Quality = is the business healthy (margins, stability, consistency)?
- **Debt / balance-sheet risk** = **8** → Balance Risk = debt + leverage + anything that can blow up fast.

## 7) Red flags (things that can hurt stock fast)
- the last twelve months revenue declining year over year (compared to last year)
- the last twelve months free cash flow (cash left after paying bills and investing in the business) declining year over year (compared to last year)
- net debt (total debt minus cash) high vs the last twelve months free cash flow (cash left after paying bills and investing in the business)
- Frequent LABOR/INSURANCE/REGULATORY negatives (30d)

## 8) Thesis test (PASS/FAIL vs your claims)
- **FAIL** — Revenue is still growing at a healthy pace  
  Metric `latest_revenue_yoy_pct` >= 10.0 | Actual: **-1.29%**
- **PASS** — Free cash flow is positive  
  Metric `latest_free_cash_flow` > 0.0 | Actual: **$11.07B**
- **FAIL** — Free cash flow margin is solid  
  Metric `latest_fcf_margin_pct` >= 10.0 | Actual: **5.99%**
- **PASS** — Valuation is not expensive versus cash (free cash flow (cash left after paying bills and investing in the business) yield is decent)  
  Metric `fcf_yield_pct` >= 3.0 | Actual: **14.19%**
- **FAIL** — Recent news shock is not severe (not a headline crisis)  
  Metric `news_shock_30d` >= -15.0 | Actual: **-23.00**
- **UNKNOWN** — Insurance risk is not spiking recently  
  Metric `risk_insurance_neg_30d` <= 3.0 | Actual: **N/A**
- **UNKNOWN** — Regulatory risk is not spiking recently  
  Metric `risk_regulatory_neg_30d` <= 3.0 | Actual: **N/A**
- **UNKNOWN** — Labor risk is not spiking recently  
  Metric `risk_labor_neg_30d` <= 3.0 | Actual: **N/A**

## 9) What to open (dopamine mode)
- Dashboard: `outputs/decision_dashboard_GM.html`
- News clickpack: `outputs/news_clickpack_GM.html`
- Alerts: `outputs/alerts_GM.json`
- Claim evidence: `outputs/claim_evidence_GM.html`

## 10) Next steps (what a human should do)
1) Open the **dashboard** first. Read rating + red flags.
2) Open the **news clickpack**. Click the top negative headlines and confirm they’re real + recent.
3) If your thesis depends on a specific risk (labor/regulatory/insurance), open **alerts** + **claim evidence**.
4) If anything looks off, treat score as directional and verify via earnings + filings.
