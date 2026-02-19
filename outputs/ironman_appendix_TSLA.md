# Iron Man Trust Appendix — TSLA
*Generated: 2026-02-19 01:10 UTC*

## What this is
This appendix explains **why the model’s news/risk signals are (or are not) trustworthy** — in plain English.

## The key idea
Not all sources are equal:
- **SEC filings** = ground truth
- **Top-tier journalism** = strong evidence
- **Aggregators** = good for *detecting* something happened, weaker for *confirming* it

So we:
1) detect spikes fast (“tactical”)
2) only escalate if **confirmed by multiple credible sources** (“institutional”)

## Tactical signal (fast)
- Articles (7d): **200**
- Negatives (7d): **9**
- News shock (7d): **-25**
- Tactical alert: **True**
> If this is True, the model is saying: “headlines are unusually negative recently.”

## Institutional confirmation (slow, trusted)
- Confirmed risk themes: **False**
- None confirmed (good: avoids single-source panic)

> A theme is *confirmed* only if it appears in multiple **independent, credible** sources.
> This prevents “one noisy outlet” from driving decisions.

## Source mix (what you should worry about)
- Top source: **finnhub**
- Top source share: **99.0%**
- Source diversity (count): **2**
- Average credibility weight: **0.7227722772277227**

If top source share is very high (like 90%+), confidence should be lower because you’re not getting independent confirmation.

## Where to click-verify
- Dashboard: `decision_dashboard_TSLA.html`
- Clickpack: `news_clickpack_TSLA.html`

**Best verification habit (60 seconds):**
1) Open clickpack
2) Click the **top negative** headlines
3) If 2+ credible sources independently report the same risk theme → treat it as real.

## Veracity score (optional)
The engine also writes `veracity_TSLA.json`. This is the machine-readable view of “how strong is the evidence mix”.
