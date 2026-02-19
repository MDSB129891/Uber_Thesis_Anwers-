#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
EXP = ROOT / "export"
DATA = ROOT / "data/processed"

OUT.mkdir(exist_ok=True)
EXP.mkdir(exist_ok=True)

def money(x):
    if x is None or pd.isna(x): return "N/A"
    return f"${x/1e9:,.2f}B"

def pct(x):
    if x is None or pd.isna(x): return "N/A"
    return f"{x:.2f}%"

def main(ticker, thesis_path):
    T = ticker.upper()

    comps = pd.read_csv(DATA/"comps_snapshot.csv")
    row = comps[comps["ticker"].str.upper()==T].iloc[0]

    fcf = row.get("fcf_ttm")
    rev_yoy = row.get("revenue_ttm_yoy_pct")
    fcf_margin = row.get("fcf_margin_ttm_pct")
    fcf_yield = row.get("fcf_yield")

    thesis = json.loads(Path(thesis_path).read_text())

    md = f"""
# BIG INVESTMENT MEMO — {T}

Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

## Your Thesis
{thesis.get("description","")}

---

## Core Numbers (human version)

• Revenue growth YoY: **{pct(rev_yoy)}**
• Free cash flow (TTM): **{money(fcf)}**
• FCF margin: **{pct(fcf_margin)}**
• FCF yield: **{pct(fcf_yield)}**

---

## What these mean (five year old mode)

Revenue growth = are people buying more?

Free cash flow = after paying bills, is cash left?

FCF margin = how much cash per $100 sales.

FCF yield = how cheap stock is vs cash.

---

## Raw Snapshot

Market cap: {money(row.get("market_cap"))}
Cash: {money(row.get("cash"))}
Debt: {money(row.get("debt"))}
Net debt: {money(row.get("net_debt"))}

---

## Model Buckets

Cash Level: {row.get("cash_level","")}
Valuation: {row.get("valuation","")}
Growth: {row.get("growth","")}
Quality: {row.get("quality","")}
Balance Risk: {row.get("balance_risk","")}

---

## Files

Dashboard: outputs/decision_dashboard_{T}.html  
News: outputs/news_clickpack_{T}.html  
Claims: outputs/claim_evidence_{T}.html  

---

End of BIG memo.
"""

    md_path = OUT/f"{T}_BIG_Memo.md"
    docx_path = EXP/f"{T}_BIG_Memo.docx"

    md_path.write_text(md,encoding="utf-8")

    from docx import Document
    doc = Document()
    for line in md.split("\n"):
        doc.add_paragraph(line)
    doc.save(docx_path)

    print("DONE ✅ BIG memo created:")
    print(md_path)
    print(docx_path)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--ticker",required=True)
    ap.add_argument("--thesis",required=True)
    a=ap.parse_args()
    main(a.ticker,a.thesis)
