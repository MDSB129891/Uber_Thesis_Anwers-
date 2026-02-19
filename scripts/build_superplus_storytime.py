#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def _fmt_pct(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return float(x)

def _fmt_billions(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return float(x) / 1e9

def _safe_upper(s):
    return str(s).strip().upper()

def load_comps_row(ticker: str) -> dict:
    p = ROOT / "data" / "processed" / "comps_snapshot.csv"
    df = pd.read_csv(p)
    df["ticker"] = df["ticker"].astype(str).str.upper()
    r = df[df["ticker"] == _safe_upper(ticker)]
    if len(r) == 0:
        raise ValueError(f"Ticker {ticker} not found in {p}")
    return r.iloc[0].to_dict()

def load_news_risk_summary(ticker: str) -> dict:
    # Prefer your generated summary if present
    p = ROOT / "outputs" / f"news_risk_summary_{_safe_upper(ticker)}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # Fallback: return Nones
    return {
        "ticker": _safe_upper(ticker),
        "news_shock_30d": None,
        "risk_labor_neg_30d": None,
        "risk_regulatory_neg_30d": None,
        "risk_insurance_neg_30d": None,
    }

def load_veracity_score(ticker: str):
    p = ROOT / "outputs" / f"veracity_{_safe_upper(ticker)}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    # your file uses confidence_score
    return d.get("confidence_score")

def load_decision_summary(ticker: str):
    p = ROOT / "outputs" / "decision_summary.json"
    if not p.exists():
        return (None, None)
    d = json.loads(p.read_text(encoding="utf-8"))
    # assumes decision_summary.json is for the current run ticker
    if _safe_upper(d.get("ticker")) != _safe_upper(ticker):
        return (None, None)
    return (d.get("rating"), d.get("score"))

def load_thesis_text(thesis_path: Path) -> str:
    d = json.loads(thesis_path.read_text(encoding="utf-8"))
    return d.get("description") or d.get("name") or "N/A"

def verdict_growth(rev_yoy):
    if rev_yoy is None: return "UNKNOWN ❓"
    if rev_yoy > 10: return "GOOD ✅"
    if rev_yoy >= 0: return "WATCH 🟡"
    return "BAD ❌"

def verdict_fcf(fcf_b):
    if fcf_b is None: return "UNKNOWN ❓"
    return "GOOD ✅" if fcf_b > 0 else "BAD ❌"

def verdict_margin(m):
    if m is None: return "UNKNOWN ❓"
    if m >= 10: return "GOOD ✅"
    if m >= 3: return "WATCH 🟡"
    return "BAD ❌"

def verdict_yield(y):
    if y is None: return "UNKNOWN ❓"
    if y > 5: return "CHEAP ✅"
    if y >= 2: return "NEUTRAL 🟡"
    return "EXPENSIVE ❌"

def verdict_debt(x):
    if x is None: return "UNKNOWN ❓"
    if x < 3: return "GOOD ✅"
    if x < 6: return "WATCH 🟡"
    return "DANGER ❌"

def verdict_shock(s):
    if s is None: return "UNKNOWN ❓"
    if s >= -15: return "CALM ✅"
    if s >= -25: return "WATCH 🟡"
    return "UGLY ❌"

def main(ticker: str, thesis_path: Path):
    T = _safe_upper(ticker)
    generated_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    comps = load_comps_row(T)
    news = load_news_risk_summary(T)
    veracity = load_veracity_score(T)
    rating, score = load_decision_summary(T)

    # core metrics
    rev_yoy = _fmt_pct(comps.get("revenue_ttm_yoy_pct"))
    fcf_b = _fmt_billions(comps.get("fcf_ttm"))
    margin = _fmt_pct(comps.get("fcf_margin_ttm_pct"))
    yld = _fmt_pct(comps.get("fcf_yield_pct"))
    if yld is None:
        # some runs store yield as decimal in fcf_yield
        fy = comps.get("fcf_yield")
        if fy is not None and not (isinstance(fy, float) and pd.isna(fy)):
            yld = float(fy) * 100.0

    net_debt = comps.get("net_debt")
    net_debt_b = _fmt_billions(net_debt) if net_debt is not None else None
    net_debt_fcf = comps.get("net_debt_to_fcf_ttm")
    net_debt_fcf = float(net_debt_fcf) if net_debt_fcf is not None and not (isinstance(net_debt_fcf, float) and pd.isna(net_debt_fcf)) else None

    thesis_text = load_thesis_text(thesis_path)

    # news risk fields
    shock_30 = news.get("news_shock_30d")
    risk_labor = news.get("risk_labor_neg_30d")
    risk_reg = news.get("risk_regulatory_neg_30d")
    risk_ins = news.get("risk_insurance_neg_30d")

    md = []
    md.append(f"# SUPERPLUS Investment Memo — {T}")
    md.append(f"*Generated: {generated_utc}*")
    md.append("")

    md.append("## 1) Your thesis (what you believe)")
    md.append(f"**{thesis_text}**")
    md.append("")

    md.append("## 2) What the model concluded (plain English)")
    md.append(f"- **Rating:** **{rating if rating is not None else 'N/A'}** (score **{score if score is not None else 'N/A'}/100**)")
    md.append(f"- **Evidence confidence:** **{veracity if veracity is not None else 'N/A'}** (higher = more trustworthy coverage)")
    md.append("")

    md.append("## 3) The 30-second explanation (for total beginners)")
    md.append(
        "Think of this like a **car dashboard**:\n\n"
        "- The **score** tells you how attractive the company looks overall.\n"
        "- The **buckets** explain *why* the score happened.\n"
        "- The **news & risk** try to spot scary headlines early.\n"
        "- The **thesis test** checks if reality matches your story.\n"
    )

    md.append("## 4) Good vs Bad cheat-sheet (linked to THIS company)")
    md.append("Each line shows: **rule → today → verdict**")
    md.append("")

    md.append("### Are sales growing?")
    md.append("- Rule: Good > 10%, OK 0–10%, Bad < 0%")
    md.append(f"- **Today:** **{rev_yoy:.2f}%** → **{verdict_growth(rev_yoy)}**" if rev_yoy is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### Is there real money left after bills? (free cash flow)")
    md.append("- Rule: Positive = good, Negative = bad")
    md.append(f"- **Today:** **${fcf_b:.2f}B** → **{verdict_fcf(fcf_b)}**" if fcf_b is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### How efficient is the business? (cash efficiency of sales)")
    md.append("- Rule: Good ≥10%, OK 3–10%, Bad ≤0%")
    md.append(f"- **Today:** **{margin:.2f}%** → **{verdict_margin(margin)}**" if margin is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### Is the stock cheap or expensive versus cash? (cash return vs stock price)")
    md.append("- Rule: Cheap >5%, Neutral 2–5%, Expensive <2%")
    md.append(f"- **Today:** **{yld:.2f}%** → **{verdict_yield(yld)}**" if yld is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### Could debt hurt if things go wrong? (years of cash to pay off debt)")
    md.append("- Rule: Good <3x, Watch 3–6x, Dangerous >6x")
    md.append(f"- **Today:** **{net_debt_fcf:.2f}x** → **{verdict_debt(net_debt_fcf)}**" if net_debt_fcf is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### Are headlines calm?")
    md.append("- Rule: Calm ≥-15, Watch -25 to -15, Ugly <-25")
    md.append(f"- **Today:** **{float(shock_30):.2f}** → **{verdict_shock(float(shock_30))}**" if shock_30 is not None else "- **Today:** **N/A** → **UNKNOWN ❓**")
    md.append("")

    md.append("### Risk headline counts (last 30 days)")
    md.append("- Rule: Low 0–2, Watch 3–5, High 6+")
    md.append(f"- Labor risk headlines: **{risk_labor if risk_labor is not None else 'N/A'}**")
    md.append(f"- Regulatory risk headlines: **{risk_reg if risk_reg is not None else 'N/A'}**")
    md.append(f"- Insurance risk headlines: **{risk_ins if risk_ins is not None else 'N/A'}**")
    md.append("")

    md.append("## 5) Storytime walkthrough (explain it like you’re five)")
    md.append(f"""
Imagine **{T}** is a **giant toy factory**.

You’re asking:

“Is this factory getting stronger… or about to run into expensive problems?”

### Step 1 — Are more toys being sold?
Sales growth is **{rev_yoy:.2f}%** compared to last year.
- If this is negative, it means fewer toys are being sold.

### Step 2 — Is there money in the piggy bank?
Free cash flow is **${fcf_b:.2f}B**.
That is what’s left after paying bills and investing.

### Step 3 — Is the factory efficient?
Cash efficiency is **{margin:.2f}%**.
That means out of every $100 of sales, about **${margin:.2f}** becomes real cash.

### Step 4 — Is the stock cheap or expensive?
Cash return vs stock price is **{yld:.2f}%**.
Higher can mean cheaper — but sometimes it’s cheap for a reason.

### Step 5 — Could debt cause stress?
Debt stress is **{net_debt_fcf:.2f}x**.
That’s roughly how many years of current cash it would take to pay off net debt.
""")

    md.append("## 6) What to open next")
    md.append(f"- Dashboard: `outputs/decision_dashboard_{T}.html`")
    md.append(f"- News clickpack: `outputs/news_clickpack_{T}.html`")
    md.append(f"- Claim evidence: `outputs/claim_evidence_{T}.html`")
    md.append("")

    out_md = ROOT / "outputs" / f"{T}_SUPERPLUS_CLEAN_Memo.md"
    out_docx = ROOT / "export" / f"{T}_SUPERPLUS_CLEAN_Memo.docx"
    out_pdf = ROOT / "export" / f"{T}_SUPERPLUS_CLEAN_Memo.pdf"

    out_md.write_text("\n".join(md).strip() + "\n", encoding="utf-8")

    # convert MD -> DOCX using your existing pipeline (fallback: write DOCX as plain text)
    # If you already have a function, replace this block with your real docx builder.
    try:
        from thesis_creator.docx_builder import build_docx_from_markdown  # if you have it
        build_docx_from_markdown(out_md.read_text(encoding="utf-8"), out_docx, f"SUPERPLUS Investment Memo — {T}")
    except Exception:
        # minimal DOCX fallback: just write markdown into docx using python-docx
        from docx import Document
        doc = Document()
        for line in out_md.read_text(encoding="utf-8").splitlines():
            doc.add_paragraph(line)
        doc.save(out_docx)

    # docx -> pdf via LibreOffice
    try:
        import subprocess
        subprocess.run(
            ["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out_pdf.parent), str(out_docx)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    print("DONE ✅ SUPERPLUS CLEAN memo created:")
    print(f"- {out_md}")
    print(f"- {out_docx}")
    print(f"- {out_pdf}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis", required=True)
    args = ap.parse_args()
    main(args.ticker, Path(args.thesis))
