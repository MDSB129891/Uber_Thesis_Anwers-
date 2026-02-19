import argparse, json, math, subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
EXP = ROOT / "export"


def _fmt_money(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "N/A"
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e12:
        return f"{sign}${x/1e12:.2f}T"
    if x >= 1e9:
        return f"{sign}${x/1e9:.2f}B"
    if x >= 1e6:
        return f"{sign}${x/1e6:.2f}M"
    return f"{sign}${x:,.0f}"


def _fmt_pct(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "N/A"
    return f"{float(x):.2f}%"


def _fmt_x(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "N/A"
    return f"{float(x):.2f}x"


def _load_comps_row(ticker: str) -> dict:
    p = DATA / "comps_snapshot.csv"
    df = pd.read_csv(p)
    df["ticker"] = df["ticker"].astype(str).str.upper()
    r = df[df["ticker"] == ticker]
    if r.empty:
        raise ValueError(f"Ticker {ticker} not found in {p}")
    return r.iloc[0].to_dict()


def _load_decision_summary(ticker: str) -> dict:
    # prefer ticker-specific, fallback to generic
    cands = [
        OUT / f"decision_summary_{ticker}.json",
        OUT / "decision_summary.json",
    ]
    for p in cands:
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            # some runs keep last ticker in decision_summary.json; that's fine.
            return d
    return {}


def _load_veracity(ticker: str) -> dict:
    p = OUT / f"veracity_{ticker}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _load_news_risk_row(ticker: str) -> dict:
    p = DATA / "news_risk_dashboard.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    # attempt common ticker col names
    for col in ["ticker", "symbol"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper()
            r = df[df[col] == ticker]
            if not r.empty:
                return r.iloc[-1].to_dict()
    return {}


def _band_label(value, bands):
    """
    bands: list of (name, predicate)
    """
    for name, fn in bands:
        try:
            if fn(value):
                return name
        except Exception:
            pass
    return "UNKNOWN ❓"


def _safe_float(x):
    try:
        if x is None:
            return None
        x = float(x)
        if math.isnan(x):
            return None
        return x
    except Exception:
        return None


def _build_md(ticker: str, thesis_path: Path) -> str:
    T = ticker.upper()
    comps = _load_comps_row(T)
    summ = _load_decision_summary(T)
    vera = _load_veracity(T)
    risk = _load_news_risk_row(T)

    thesis = json.loads(thesis_path.read_text(encoding="utf-8"))
    thesis_title = thesis.get("name") or thesis.get("headline") or f"{T}: Thesis"
    thesis_text = thesis.get("thesis") or thesis.get("description") or thesis.get("summary") or ""

    # Core metrics (from comps_snapshot)
    rev_y = _safe_float(comps.get("revenue_ttm_yoy_pct"))
    fcf_ttm = _safe_float(comps.get("fcf_ttm"))
    fcf_m = _safe_float(comps.get("fcf_margin_ttm_pct"))
    fcf_yield_pct = _safe_float(comps.get("fcf_yield_pct"))  # may be missing in some builds
    if fcf_yield_pct is None:
        # some versions store yield as decimal in "fcf_yield"
        fy = _safe_float(comps.get("fcf_yield"))
        if fy is not None:
            fcf_yield_pct = fy * 100.0

    mcap = _safe_float(comps.get("market_cap"))
    cash = _safe_float(comps.get("cash"))
    debt = _safe_float(comps.get("debt"))
    net_debt = _safe_float(comps.get("net_debt"))
    nd_to_fcf = _safe_float(comps.get("net_debt_to_fcf_ttm"))

    # News/risk
    news_shock = _safe_float(risk.get("news_shock_30d")) or _safe_float(comps.get("news_shock_30d"))
    r_labor = _safe_float(risk.get("risk_labor_neg_30d"))
    r_reg = _safe_float(risk.get("risk_regulatory_neg_30d"))
    r_ins = _safe_float(risk.get("risk_insurance_neg_30d"))

    rating = summ.get("rating") or summ.get("verdict") or "N/A"
    score = summ.get("score") or summ.get("total_score") or "N/A"
    veracity_score = vera.get("veracity_score") or vera.get("score") or vera.get("confidence_score") or "N/A"

    # Cheat-sheet verdicts linked to today’s values
    rev_verdict = _band_label(
        rev_y,
        [
            ("GOOD ✅", lambda v: v is not None and v > 10),
            ("OK 🟡", lambda v: v is not None and 0 <= v <= 10),
            ("BAD ❌", lambda v: v is not None and v < 0),
        ],
    )
    fcf_verdict = _band_label(
        fcf_ttm,
        [
            ("GOOD ✅", lambda v: v is not None and v > 0),
            ("BAD ❌", lambda v: v is not None and v <= 0),
        ],
    )
    fcfm_verdict = _band_label(
        fcf_m,
        [
            ("GOOD ✅", lambda v: v is not None and v >= 10),
            ("OK 🟡", lambda v: v is not None and 3 <= v < 10),
            ("BAD ❌", lambda v: v is not None and v <= 0),
        ],
    )
    fcfy_verdict = _band_label(
        fcf_yield_pct,
        [
            ("GOOD ✅", lambda v: v is not None and v > 5),
            ("OK 🟡", lambda v: v is not None and 2 <= v <= 5),
            ("EXPENSIVE ❌", lambda v: v is not None and v < 2),
        ],
    )
    nd_fcf_verdict = _band_label(
        nd_to_fcf,
        [
            ("GOOD ✅", lambda v: v is not None and v < 3),
            ("WATCH 🟡", lambda v: v is not None and 3 <= v <= 6),
            ("HIGH RISK ❌", lambda v: v is not None and v > 6),
        ],
    )

    # Simple “thesis breaker” callouts for employee reclassification
    thesis_break = f"""
## 7) If your thesis is about drivers becoming employees (what breaks first)

If drivers must be treated as employees, Uber typically sees costs rise in a very specific order:

1) **Cost per trip rises** (wages + benefits + payroll taxes + scheduling + compliance).
2) That tends to hit **cash left over after all bills** first (free cash flow), and also the **cash efficiency of sales** (free cash flow margin).
3) If markets believe the change is durable, investors may pay **less per dollar of cash**, which can pressure the stock price.

**Weekly “watch list”**
- Labor / regulation headlines (court cases, ballots, bills)
- Any language in earnings calls/filings about classification rules and cost impacts
- Movement in “risk” signals: labor/regulatory negatives rising over 30 days
""".strip()

    md = f"""# SUPER+ Investment Memo — {T}
*Generated: {pd.Timestamp.utcnow():%Y-%m-%d %H:%M UTC}*

## 1) Your thesis (what you believe)
**{thesis_title}**
{thesis_text}

## 2) What the model concluded (plain English)
- **Rating:** **{rating}** (score **{score}/100**)
- **Evidence confidence / veracity:** **{veracity_score}** (higher = more trustworthy coverage)

## 3) The 30-second explanation (for total beginners)
Think of this like a **car dashboard**:
- The **score** is the overall attractiveness estimate.
- The **buckets** explain *why* the score happened.
- The **news/risk** items try to spot headline landmines.
- The **thesis test** checks whether the facts match the story you’re betting on.

## Good vs Bad cheat-sheet (linked to this ticker)
Each line shows: **rule band → today’s value → verdict**.

### Revenue growth compared to last year
- Rule band: Usually good **> +10%** | OK **0% to +10%** | Usually bad **< 0%**
- **{T} today:** **{_fmt_pct(rev_y)}** → **{rev_verdict}**

### Cash left over after all bills over the last 12 months (free cash flow)
- Rule band: Good **positive** | Bad **negative**
- **{T} today:** **{_fmt_money(fcf_ttm)}** → **{fcf_verdict}**

### Cash efficiency of sales (free cash flow margin)
- Rule band: Usually good **≥ 10%** | OK **3% to 10%** | Bad **≤ 0%**
- **{T} today:** **{_fmt_pct(fcf_m)}** → **{fcfm_verdict}**

### Cash return vs stock price (free cash flow yield)
- Rule band: Often cheap **> 5%** | Neutral **2% to 5%** | Often expensive **< 2%**
- **{T} today:** **{_fmt_pct(fcf_yield_pct)}** → **{fcfy_verdict}**

### Debt stress (net debt divided by free cash flow)
- Rule band: Good **< 3x** | Watch **3x to 6x** | High risk **> 6x**
- **{T} today:** **{_fmt_x(nd_to_fcf)}** → **{nd_fcf_verdict}**

## 4) Core numbers (sanity-check)
- Revenue growth compared to last year: **{_fmt_pct(rev_y)}**  _(comps_snapshot → revenue_ttm_yoy_pct)_
- Cash left over after all bills (last 12 months): **{_fmt_money(fcf_ttm)}**  _(comps_snapshot → fcf_ttm)_
- Cash efficiency of sales: **{_fmt_pct(fcf_m)}**  _(comps_snapshot → fcf_margin_ttm_pct)_
- Cash return vs price paid: **{_fmt_pct(fcf_yield_pct)}**  _(comps_snapshot → fcf_yield_pct / fcf_yield)_

## 5) Balance sheet snapshot (why debt matters)
- Market cap: **{_fmt_money(mcap)}**
- Cash: **{_fmt_money(cash)}**
- Debt: **{_fmt_money(debt)}**
- Net debt (debt minus cash): **{_fmt_money(net_debt)}**
- Net debt divided by free cash flow: **{_fmt_x(nd_to_fcf)}**

## 6) News & risk quick check (last 30 days)
- Negative headline shock score: **{news_shock if news_shock is not None else "N/A"}**
- Labor risk negatives (30d): **{r_labor if r_labor is not None else "N/A"}**
- Regulatory risk negatives (30d): **{r_reg if r_reg is not None else "N/A"}**
- Insurance risk negatives (30d): **{r_ins if r_ins is not None else "N/A"}**

{thesis_break}

## 8) What to open (dopamine mode)
- Dashboard: `outputs/decision_dashboard_{T}.html`
- News clickpack: `outputs/news_clickpack_{T}.html`
- Alerts: `outputs/alerts_{T}.json`
- Claim evidence: `outputs/claim_evidence_{T}.html`
""".strip()

    return md


def _md_to_docx(md_path: Path, docx_path: Path):
    # Minimal conversion: wrap into a docx using LibreOffice via "text" import
    # (Works reliably; your pipeline already uses soffice for docx->pdf)
    # Create a temporary .txt and let LO import it.
    tmp = docx_path.with_suffix(".txt")
    tmp.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    # convert txt -> docx
    cmd = ["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "docx", "--outdir", str(docx_path.parent), str(tmp)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # LibreOffice names output with .docx from tmp
    produced = tmp.with_suffix(".docx")
    if produced.exists():
        produced.replace(docx_path)
    try:
        tmp.unlink()
    except Exception:
        pass


def _docx_to_pdf(docx_path: Path, pdf_path: Path):
    cmd = ["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "pdf", "--outdir", str(pdf_path.parent), str(docx_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    produced = docx_path.with_suffix(".pdf")
    if produced.exists() and produced != pdf_path:
        produced.replace(pdf_path)


def main(ticker: str, thesis: Path):
    T = ticker.upper()
    OUT.mkdir(parents=True, exist_ok=True)
    EXP.mkdir(parents=True, exist_ok=True)

    md = _build_md(T, thesis)
    md_path = OUT / f"{T}_SUPERPLUS_Memo.md"
    docx_path = EXP / f"{T}_SUPERPLUS_Memo.docx"
    pdf_path = EXP / f"{T}_SUPERPLUS_Memo.pdf"

    md_path.write_text(md, encoding="utf-8")
    _md_to_docx(md_path, docx_path)
    if docx_path.exists():
        _docx_to_pdf(docx_path, pdf_path)

    print("DONE ✅ SUPERPLUS memo created:")
    print("-", md_path)
    print("-", docx_path)
    print("-", pdf_path if pdf_path.exists() else "(pdf missing)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis", required=True)
    args = ap.parse_args()
    main(args.ticker, Path(args.thesis))
