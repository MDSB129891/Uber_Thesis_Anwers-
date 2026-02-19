#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from datetime import datetime
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
EXPORT = ROOT / "export"

def utc_now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")



def build_deadline_explainers(summary, metrics):
    lines = []
    lines.append("## How to read this report (plain English)")
    lines.append("")
    lines.append("This system looks at five things:")
    lines.append("")
    lines.append("- Cash: does the company actually generate money?")
    lines.append("- Valuation: are you overpaying for that cash?")
    lines.append("- Growth: are revenues expanding?")
    lines.append("- Quality: margins + consistency.")
    lines.append("- Risk: debt + bad news trends.")
    lines.append("")
    lines.append("Scores closer to 100 mean stronger fundamentals and lower risk.")
    lines.append("")
    lines.append("### Important metrics explained")
    lines.append("")
    lines.append("- Revenue YoY: how fast sales are growing.")
    lines.append("- Free Cash Flow: real money left after expenses.")
    lines.append("- FCF Margin: percent of revenue kept as cash.")
    lines.append("- FCF Yield: cash return vs stock price.")
    lines.append("- News shock: recent negative headlines intensity.")
    lines.append("")
    lines.append("Rough guide:")
    lines.append("- Revenue growth >10% = healthy")
    lines.append("- FCF positive = company funds itself")
    lines.append("- FCF margin >10% = strong business")
    lines.append("- FCF yield >3% = valuation reasonable")
    lines.append("- News shock worse than -20 = headline crisis")
    lines.append("")
    return lines

def main(ticker, thesis_path=None):
    ticker = ticker.upper()

    summary = json.load(open(OUTPUTS / "decision_summary.json"))
    alerts = json.load(open(OUTPUTS / f"alerts_{ticker}.json")) if (OUTPUTS / f"alerts_{ticker}.json").exists() else {}

    rating = summary.get("rating")
    score = summary.get("score")

    md = []
    md.append(f"# Full Investment Memo — {ticker}")
    md.append(f"*Generated: {utc_now()}*")
    md.append("")
    md.append("## Quick summary")
    md.append(f"- Model rating: **{rating}** ({score}/100)")
    md.append("")

    if alerts:
        md.append("## Red flags")
        for r in alerts.get("red_flags", []):
            md.append(f"- {r}")
        md.append("")

    md.append("## What to open")
    md.append(f"- PDF: export/{ticker}_Full_Investment_Memo.pdf")
    md.append(f"- Dashboard: outputs/decision_dashboard_{ticker}.html")
    md.append(f"- News: outputs/news_clickpack_{ticker}.html")
    md.append("")

    md.append("## Plain English")
    md.append("This report combines financials, valuation, growth, balance sheet, and recent news.")
    md.append("Higher scores mean stronger business quality and lower risk.")
    md.append("")

    md.append("## Verdict")
    if rating == "BUY":
        md.append("Business fundamentals currently outweigh risks.")
    elif rating == "HOLD":
        md.append("Mixed signals. Wait for clearer direction.")
    else:
        md.append("Risks dominate fundamentals right now.")

    md_path = OUTPUTS / f"{ticker}_Full_Investment_Memo.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    doc = Document()
    for line in md:
        doc.add_paragraph(line)

    EXPORT.mkdir(exist_ok=True)
    docx_path = EXPORT / f"{ticker}_Full_Investment_Memo.docx"
    doc.save(docx_path)

    print(f"DONE Memo created:")
    print("-", md_path)
    print("-", docx_path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis")
    args = ap.parse_args()
    main(args.ticker, args.thesis)
