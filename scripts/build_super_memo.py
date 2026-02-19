#!/usr/bin/env python3
import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
EXP = ROOT / "export"
DATA = ROOT / "data" / "processed"

OUT.mkdir(parents=True, exist_ok=True)
EXP.mkdir(parents=True, exist_ok=True)

ABBR = [
    (r"\bYoY\b", "compared to last year"),
    (r"\bTTM\b", "over the last 12 months"),
    (r"\bFCF\b", "free cash flow"),
    (r"\bEV\b", "enterprise value"),
    (r"\bEBITDA\b", "earnings before interest, taxes, depreciation, and amortization"),
]

def _is_nan(x) -> bool:
    try:
        return x is None or (isinstance(x, float) and math.isnan(x))
    except Exception:
        return False

def _fmt_pct(x, digits=2):
    if _is_nan(x): return "N/A"
    try: return f"{float(x):.{digits}f}%"
    except Exception: return "N/A"

def _fmt_money(x):
    if _is_nan(x): return "N/A"
    try:
        x = float(x)
        sign = "-" if x < 0 else ""
        x = abs(x)
        if x >= 1e12: return f"{sign}${x/1e12:.2f}T"
        if x >= 1e9:  return f"{sign}${x/1e9:.2f}B"
        if x >= 1e6:  return f"{sign}${x/1e6:.2f}M"
        return f"{sign}${x:,.0f}"
    except Exception:
        return "N/A"

def _fmt_x(x, digits=2):
    if _is_nan(x): return "N/A"
    try: return f"{float(x):.{digits}f}x"
    except Exception: return "N/A"

def _de_jargon(text: str) -> str:
    out = text
    for pat, rep in ABBR:
        out = re.sub(pat, rep, out)
    # Cleanup weird bullets that come from Word conversions sometimes
    out = out.replace("", "- ").replace("•", "- ")
    return out

def _read_json(p: Path, default=None):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))

def _load_comps_row(ticker: str) -> dict:
    p = DATA / "comps_snapshot.csv"
    if not p.exists():
        raise FileNotFoundError(f"Missing comps snapshot: {p}")
    df = pd.read_csv(p)
    df["ticker"] = df["ticker"].astype(str).str.upper()
    r = df[df["ticker"] == ticker.upper()]
    if len(r) == 0:
        raise ValueError(f"Ticker {ticker} not found in {p}")
    return r.iloc[0].to_dict()

def _now_utc_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

CHEATSHEET = """
## Good vs Bad cheat-sheet (how to judge the numbers)

Think of every metric like a **warning light** on a car.

### Revenue growth compared to last year
- ✅ Usually good: **more than +10%**
- 🟡 Depends: **0% to +10%**
- ❌ Usually bad: **below 0%** (shrinking sales)

### Free cash flow
- ✅ Good: **positive** and steady/rising
- 🟡 Mixed: small positive but bouncy
- ❌ Bad: negative often (burning cash)

### Free cash flow margin
- ✅ Good: **10% or higher** (industry dependent)
- 🟡 Mixed: **3% to 10%**
- ❌ Bad: **0% or negative**

### Free cash flow yield (cash vs what you pay for the stock)
- ✅ Often cheap: **above 5%**
- 🟡 Neutral: **2% to 5%**
- ❌ Often expensive: **below 2%**

### Net debt (debt minus cash)
- ✅ Better: low net debt (or net cash)
- 🟡 Watch: moderate net debt if cash is strong
- ❌ Risky: big net debt while cash is weakening

### Net debt divided by free cash flow (years-to-pay debt)
- ✅ Good: **below 3x**
- 🟡 Watch: **3x to 6x**
- ❌ High risk: **above 6x**
""".strip()

def _storytime_block(ticker: str, rev_g: str, fcf: str, fcf_m: str, fcf_y: str, net_debt_x: str) -> str:
    return f"""
## Storytime walkthrough (explain it like I’m five)

Okay. Imagine **{ticker}** is a **gigantic toy factory**.

You (the investor) are basically asking:
> “Is this toy factory going to make **more money later**, or get hit with **expensive problems**?”

### Step A — Sales (revenue)
“Revenue growth compared to last year” means: **are more kids buying the toys this year, or fewer?**
- Today it shows: **{rev_g}**.

If this number is negative, it means **fewer toys are being sold** than last year (usually not great).

### Step B — Real cash (free cash flow)
“Free cash flow” means: after paying for everything **and** investing in the business… is there money left in the piggy bank?
- Today it shows: **{fcf}**.

Positive = piggy bank fills. Negative = piggy bank leaks.

### Step C — Efficiency (free cash flow margin)
This is: out of every **$100** of toy sales, how many dollars become free cash?
- Today it shows: **{fcf_m}**.

### Step D — Price vs cash (free cash flow yield)
This is: if you buy the whole factory at today’s stock price, how much free cash do you get back each year?
- Today it shows: **{fcf_y}**.

### Step E — Debt stress (net debt / free cash flow)
This is: how many “years of piggy-bank money” it would take to pay off debt.
- Today it shows: **{net_debt_x}**.

Higher numbers here mean **less flexibility** if something goes wrong.
""".strip()

def _docx_from_markdown(md_text: str, docx_path: Path):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    for line in md_text.splitlines():
        line = line.rstrip()
        if not line:
            doc.add_paragraph("")
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("- "):
            p = doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)

    doc.save(str(docx_path))

def _export_pdf(docx_path: Path, outdir: Path):
    # Uses LibreOffice
    soffice = "/opt/homebrew/bin/soffice"
    if not Path(soffice).exists():
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(docx_path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pdf_path = outdir / (docx_path.stem + ".pdf")
        return pdf_path if pdf_path.exists() else None
    except Exception:
        return None

def main(ticker: str, thesis_path: Path):
    T = ticker.upper()

    comps = _load_comps_row(T)

    # Pull core numbers from comps_snapshot
    rev_g = _fmt_pct(comps.get("revenue_ttm_yoy_pct"))
    fcf_ttm = comps.get("fcf_ttm")
    fcf = _fmt_money(fcf_ttm)
    fcf_m = _fmt_pct(comps.get("fcf_margin_ttm_pct"))
    # sometimes yield stored as fcf_yield_pct or fcf_yield (fraction)
    fy_pct = comps.get("fcf_yield_pct")
    if _is_nan(fy_pct):
        fy = comps.get("fcf_yield")
        if not _is_nan(fy):
            try:
                fy_pct = float(fy) * 100.0
            except Exception:
                fy_pct = None
    fcf_y = _fmt_pct(fy_pct)

    cash = comps.get("cash")
    debt = comps.get("debt")
    net_debt = comps.get("net_debt")
    net_debt_to_fcf = comps.get("net_debt_to_fcf_ttm")

    # decision summary + veracity if present
    decision = _read_json(OUT / "decision_summary.json", default={}) or {}
    veracity = _read_json(OUT / f"veracity_{T}.json", default={}) or {}
    rating = decision.get("rating") or decision.get("verdict") or "N/A"
    score = decision.get("score") if decision.get("score") is not None else "N/A"
    veracity_score = veracity.get("confidence_score") or veracity.get("veracity_score") or veracity.get("confidence") or "N/A"

    buckets = decision.get("bucket_scores") or decision.get("buckets") or {}
    red_flags = decision.get("red_flags") or []

    thesis = _read_json(thesis_path, default={}) or {}
    thesis_title = thesis.get("headline") or thesis.get("title") or f"{T}: Thesis"
    thesis_text = thesis.get("thesis") or thesis.get("description") or thesis.get("one_paragraph") or "N/A"

    # claims (if any)
    claims = thesis.get("claims") or []
    # alerts / evidence references (files)
    dashboard = f"outputs/decision_dashboard_{T}.html"
    news_clickpack = f"outputs/news_clickpack_{T}.html"
    alerts_json = f"outputs/alerts_{T}.json"
    claim_html = f"outputs/claim_evidence_{T}.html"

    md = []
    md.append(f"# SUPER Investment Memo — {T}")
    md.append(f"*Generated: {_now_utc_str()}*")
    md.append("")
    md.append("## 1) Your thesis (what you believe)")
    md.append(f"**{thesis_title}**")
    md.append(f"{thesis_text}")
    md.append("")
    md.append("## 2) What the model concluded (plain English)")
    md.append(f"- **Rating:** **{rating}** (score **{score}/100**)")
    md.append(f"- **Evidence confidence / veracity:** **{veracity_score}** (higher = more trustworthy coverage)")
    md.append("")
    md.append("## 3) The 30-second explanation (for total beginners)")
    md.append("Think of this like a **car dashboard**:")
    md.append("- The **score** is the overall attractiveness estimate.")
    md.append("- The **buckets** explain *why* the score happened.")
    md.append("- The **news/risk** items try to spot headline landmines.")
    md.append("- The **thesis test** checks whether the facts match the story you’re betting on.")
    md.append("")
    md.append(CHEATSHEET)
    md.append("")
    md.append("## 4) Core numbers (sanity-check)")
    md.append(f"- Revenue growth compared to last year: **{rev_g}**  _(source: comps_snapshot → revenue_ttm_yoy_pct)_")
    md.append(f"- Free cash flow over the last 12 months: **{fcf}**  _(source: comps_snapshot → fcf_ttm)_")
    md.append(f"- Free cash flow margin: **{fcf_m}**  _(source: comps_snapshot → fcf_margin_ttm_pct)_")
    md.append(f"- Free cash flow yield: **{fcf_y}**  _(source: comps_snapshot → fcf_yield_pct / fcf_yield)_")
    md.append("")
    md.append("## 5) Balance sheet snapshot (why debt matters)")
    md.append(f"- Market cap: **{_fmt_money(comps.get('market_cap'))}**")
    md.append(f"- Cash: **{_fmt_money(cash)}**")
    md.append(f"- Debt: **{_fmt_money(debt)}**")
    md.append(f"- Net debt: **{_fmt_money(net_debt)}**  _(debt minus cash)_")
    md.append(f"- Net debt divided by free cash flow: **{_fmt_x(net_debt_to_fcf)}**  _(how many years of cash it takes to pay debt)_")
    md.append("")
    md.append("## 6) Bucket scores (what drove the rating)")
    if isinstance(buckets, dict) and buckets:
        for k, v in buckets.items():
            md.append(f"- **{k}** = **{v}**")
    else:
        md.append("- N/A")
    md.append("")
    md.append("## 7) Red flags (things that can hurt stock fast)")
    if red_flags:
        for rf in red_flags:
            md.append(f"- {rf}")
    else:
        md.append("- None detected")
    md.append("")
    md.append("## 8) Thesis test (PASS/FAIL vs your claims)")
    if claims:
        for c in claims:
            name = c.get("name") or c.get("label") or "Claim"
            metric = c.get("metric") or "metric"
            op = c.get("op") or c.get("operator") or ""
            thr = c.get("threshold")
            md.append(f"- **{name}** — `{metric}` {op} {thr}")
    else:
        md.append("- No claims provided in thesis file (optional).")
    md.append("")
    md.append(_storytime_block(T, rev_g, fcf, fcf_m, fcf_y, _fmt_x(net_debt_to_fcf)))
    md.append("")
    md.append("## 9) What to open (dopamine mode)")
    md.append(f"- Dashboard: `{dashboard}`")
    md.append(f"- News clickpack: `{news_clickpack}`")
    md.append(f"- Alerts: `{alerts_json}`")
    md.append(f"- Claim evidence: `{claim_html}`")
    md.append("")
    md.append("## 10) Next steps (what a human should do)")
    md.append("1) Open the **dashboard** first. Read rating + red flags.")
    md.append("2) Open the **news clickpack**. Click the top negative headlines and confirm they’re real + recent.")
    md.append("3) If your thesis depends on a specific risk (labor/regulatory/insurance), open **alerts** + **claim evidence**.")
    md.append("4) If anything looks off, treat score as directional and verify via earnings + filings.")
    md.append("")

    md_text = _de_jargon("\n".join(md))

    md_path = OUT / f"{T}_SUPER_Memo.md"
    docx_path = EXP / f"{T}_SUPER_Memo.docx"

    md_path.write_text(md_text, encoding="utf-8")
    _docx_from_markdown(md_text, docx_path)

    pdf_path = _export_pdf(docx_path, EXP)

    print("DONE ✅ SUPER memo created:")
    print(f"- {md_path}")
    print(f"- {docx_path}")
    if pdf_path:
        print(f"- {pdf_path}")
    else:
        print("⚠️ PDF export failed (LibreOffice not available or conversion failed).")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis", required=True, help="Path to thesis json")
    args = ap.parse_args()
    main(args.ticker, Path(args.thesis))
