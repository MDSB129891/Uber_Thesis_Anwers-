from pathlib import Path

P = Path("scripts/build_investment_memo.py")

txt = P.read_text(encoding="utf-8")

INSERT = """

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

"""

if "build_deadline_explainers" not in txt:
    idx = txt.find("def main(")
    txt = txt[:idx] + INSERT + txt[idx:]

MARK = "md.append(build_next_steps())"

if MARK in txt:
    txt = txt.replace(
        MARK,
        MARK + "\n    md.extend(build_deadline_explainers(decision_summary, metrics))\n"
    )

P.write_text(txt, encoding="utf-8")
print("DONE ✅ Deadline explainer injected")
