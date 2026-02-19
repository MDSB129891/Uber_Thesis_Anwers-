# SUPER Investment Memo — GM
*Generated: 2026-02-19 15:58 UTC*

## 1) Your thesis (what you believe)
**GM: Thesis**
enterprise value expansion drives margin recovery

## 2) What the model concluded (plain English)
- **Rating:** **AVOID** (score **52/100**)
- **Evidence confidence / veracity:** **46** (higher = more trustworthy coverage)

## 3) The 30-second explanation (for total beginners)
Think of this like a **car dashboard**:
- The **score** is the overall attractiveness estimate.
- The **buckets** explain *why* the score happened.
- The **news/risk** items try to spot headline landmines.
- The **thesis test** checks whether the facts match the story you’re betting on.

## Good vs Bad cheat-sheet (linked to this ticker)

Think of each metric like a **warning light**. Below is the rule, then **GM today**.

### Revenue growth compared to last year
- **Rule band:** below 0%
- **GM today:** **-1.29%** → **❌ BAD**

### Free cash flow (cash left after paying bills + investment)
- **Rule band:** positive
- **GM today:** **$11.07B** → **✅ GOOD**

### Free cash flow margin (cash per $100 of sales)
- **Rule band:** 3% to 10%
- **GM today:** **5.99%** → **🟡 WATCH**

### Free cash flow yield (cash vs what you pay for the stock)
- **Rule band:** above 5%
- **GM today:** **14.19%** → **✅ GOOD**

### Net debt (debt minus cash)
- **GM today:** debt **$130.28B**, cash **$20.95B**, net debt **$109.33B** → **🟡 WATCH**

### Net debt divided by free cash flow (years-to-pay debt)
- **Rule band:** above 6x
- **GM today:** **9.87x** → **❌ BAD**
## 4) Core numbers (sanity-check)
- Revenue growth compared to last year: **-1.29%**  _(source: comps_snapshot → revenue_ttm_yoy_pct)_
- Free cash flow over the last 12 months: **$11.07B**  _(source: comps_snapshot → fcf_ttm)_
- Free cash flow margin: **5.99%**  _(source: comps_snapshot → fcf_margin_ttm_pct)_
- Free cash flow yield: **14.19%**  _(source: comps_snapshot → fcf_yield_pct / fcf_yield)_

## 5) Balance sheet snapshot (why debt matters)
- Market cap: **$78.05B**
- Cash: **$20.95B**
- Debt: **$130.28B**
- Net debt: **$109.33B**  _(debt minus cash)_
- Net debt divided by free cash flow: **9.87x**  _(how many years of cash it takes to pay debt)_

## 6) Bucket scores (what drove the rating)
- **cash_level** = **21**
- **valuation** = **17**
- **growth** = **0**
- **quality** = **6**
- **balance_risk** = **8**

## 7) Red flags (things that can hurt stock fast)
- over the last 12 months revenue declining compared to last year
- over the last 12 months free cash flow declining compared to last year
- Net debt high vs over the last 12 months free cash flow
- Frequent LABOR/INSURANCE/REGULATORY negatives (30d)

## 8) Thesis test (PASS/FAIL vs your claims)
- **Claim** — `latest_revenue_yoy_pct` >= 10.0
- **Claim** — `latest_free_cash_flow` > 0.0
- **Claim** — `latest_fcf_margin_pct` >= 10.0
- **Claim** — `fcf_yield_pct` >= 3.0
- **Claim** — `news_shock_30d` >= -15.0
- **Claim** — `risk_insurance_neg_30d` <= 3.0
- **Claim** — `risk_regulatory_neg_30d` <= 3.0
- **Claim** — `risk_labor_neg_30d` <= 3.0

## Storytime walkthrough (explain it like I’m five)

Okay. Imagine **GM** is a **gigantic toy factory**.

You (the investor) are basically asking:
> “Is this toy factory going to make **more money later**, or get hit with **expensive problems**?”

### Step A — Sales (revenue)
“Revenue growth compared to last year” means: **are more kids buying the toys this year, or fewer?**
- Today it shows: **-1.29%**.

If this number is negative, it means **fewer toys are being sold** than last year (usually not great).

### Step B — Real cash (free cash flow)
“Free cash flow” means: after paying for everything **and** investing in the business… is there money left in the piggy bank?
- Today it shows: **$11.07B**.

Positive = piggy bank fills. Negative = piggy bank leaks.

### Step C — Efficiency (free cash flow margin)
This is: out of every **$100** of toy sales, how many dollars become free cash?
- Today it shows: **5.99%**.

### Step D — Price vs cash (free cash flow yield)
This is: if you buy the whole factory at today’s stock price, how much free cash do you get back each year?
- Today it shows: **14.19%**.

### Step E — Debt stress (net debt / free cash flow)
This is: how many “years of piggy-bank money” it would take to pay off debt.
- Today it shows: **9.87x**.

Higher numbers here mean **less flexibility** if something goes wrong.

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
