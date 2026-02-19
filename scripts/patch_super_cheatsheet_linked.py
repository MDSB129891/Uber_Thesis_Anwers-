import re
import math
import pandas as pd
from pathlib import Path
import argparse

def is_na(x):
    return x is None or (isinstance(x, float) and (math.isnan(x) or pd.isna(x)))

def pct(x, digits=2):
    if is_na(x): return "N/A"
    return f"{float(x):.{digits}f}%"

def money(x):
    if is_na(x): return "N/A"
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e12: return f"{sign}${x/1e12:.2f}T"
    if x >= 1e9:  return f"{sign}${x/1e9:.2f}B"
    if x >= 1e6:  return f"{sign}${x/1e6:.2f}M"
    return f"{sign}${x:,.0f}"

def xmult(x, digits=2):
    if is_na(x): return "N/A"
    return f"{float(x):.{digits}f}x"

def classify_revenue_growth(v):
    if is_na(v): return ("UNKNOWN", "N/A")
    v = float(v)
    if v > 10: return ("GOOD", "more than +10%")
    if v >= 0: return ("WATCH", "0% to +10%")
    return ("BAD", "below 0%")

def classify_fcf(v):
    if is_na(v): return ("UNKNOWN", "N/A")
    v = float(v)
    if v > 0: return ("GOOD", "positive")
    return ("BAD", "negative")

def classify_fcf_margin(v):
    if is_na(v): return ("UNKNOWN", "N/A")
    v = float(v)
    if v >= 10: return ("GOOD", "10% or higher")
    if v >= 3: return ("WATCH", "3% to 10%")
    return ("BAD", "0% to 3% (or negative)")

def classify_fcf_yield(v):
    if is_na(v): return ("UNKNOWN", "N/A")
    v = float(v)
    if v > 5: return ("GOOD", "above 5%")
    if v >= 2: return ("WATCH", "2% to 5%")
    return ("BAD", "below 2%")

def classify_net_debt(nd):
    if is_na(nd): return ("UNKNOWN", "N/A")
    nd = float(nd)
    if nd <= 0: return ("GOOD", "net cash (<= 0)")
    # If positive net debt, we mark WATCH unless it’s extreme (we’ll rely more on net debt/FCF below)
    return ("WATCH", "positive net debt")

def classify_net_debt_to_fcf(x):
    if is_na(x): return ("UNKNOWN", "N/A")
    x = float(x)
    if x < 3: return ("GOOD", "below 3x")
    if x <= 6: return ("WATCH", "3x to 6x")
    return ("BAD", "above 6x")

def verdict_badge(v):
    # Simple, consistent labels for humans
    return {
        "GOOD": "✅ GOOD",
        "WATCH": "🟡 WATCH",
        "BAD": "❌ BAD",
        "UNKNOWN": "❓ UNKNOWN"
    }.get(v, v)

def load_comps_row(ticker: str):
    p = Path("data/processed/comps_snapshot.csv")
    df = pd.read_csv(p)
    df["ticker"] = df["ticker"].astype(str).str.upper()
    r = df[df["ticker"] == ticker.upper()]
    if r.empty:
        raise SystemExit(f"Ticker {ticker} not found in {p}")
    return r.iloc[0].to_dict()

def build_linked_cheatsheet(ticker: str, row: dict) -> str:
    # Pull values (these exist in your file per earlier prints)
    rev_yoy = row.get("revenue_ttm_yoy_pct")
    fcf_ttm = row.get("fcf_ttm")
    fcf_margin = row.get("fcf_margin_ttm_pct")
    # fcf_yield can be in pct or decimal depending on your pipeline; prefer *_pct if exists
    fcf_yield_pct = row.get("fcf_yield_pct")
    if is_na(fcf_yield_pct):
        fy = row.get("fcf_yield")
        if not is_na(fy):
            # If it's decimal (0.14), convert to %
            fcf_yield_pct = float(fy) * (100.0 if float(fy) <= 1 else 1.0)

    cash = row.get("cash")
    debt = row.get("debt")
    net_debt = row.get("net_debt")
    nd_to_fcf = row.get("net_debt_to_fcf_ttm")

    # Classify
    g1, b1 = classify_revenue_growth(rev_yoy)
    g2, b2 = classify_fcf(fcf_ttm)
    g3, b3 = classify_fcf_margin(fcf_margin)
    g4, b4 = classify_fcf_yield(fcf_yield_pct)
    g5, b5 = classify_net_debt(net_debt)
    g6, b6 = classify_net_debt_to_fcf(nd_to_fcf)

    lines = []
    lines.append("## Good vs Bad cheat-sheet (linked to this ticker)\n")
    lines.append(f"Think of each metric like a **warning light**. Below is the rule, then **{ticker.upper()} today**.\n")

    def block(title, rule_band, today_str, verdict):
        return (
            f"### {title}\n"
            f"- **Rule band:** {rule_band}\n"
            f"- **{ticker.upper()} today:** **{today_str}** → **{verdict_badge(verdict)}**\n"
        )

    lines.append(block("Revenue growth compared to last year", b1, pct(rev_yoy), g1))
    lines.append(block("Free cash flow (cash left after paying bills + investment)", b2, money(fcf_ttm), g2))
    lines.append(block("Free cash flow margin (cash per $100 of sales)", b3, pct(fcf_margin), g3))
    lines.append(block("Free cash flow yield (cash vs what you pay for the stock)", b4, pct(fcf_yield_pct), g4))
    # extra context for debt
    lines.append(
        f"### Net debt (debt minus cash)\n"
        f"- **GM today:** debt **{money(debt)}**, cash **{money(cash)}**, net debt **{money(net_debt)}** → **{verdict_badge(g5)}**\n"
    )
    lines.append(block("Net debt divided by free cash flow (years-to-pay debt)", b6, xmult(nd_to_fcf), g6))

    lines.append("\n")
    return "\n".join(lines)

def replace_section(md_text: str, new_section: str) -> str:
    # Replace any existing cheat-sheet section, or insert after intro if missing
    pat = r"(?s)## Good vs Bad cheat-sheet.*?(?=\n## |\Z)"
    if re.search(pat, md_text):
        return re.sub(pat, new_section.rstrip(), md_text)
    # Insert after the 30-second explanation block if present
    anchor = r"(?s)(## 3\) The 30-second explanation.*?\n)(?=## )"
    m = re.search(anchor, md_text)
    if m:
        return md_text[:m.end(1)] + "\n" + new_section + "\n" + md_text[m.end(1):]
    # else just append
    return md_text.rstrip() + "\n\n" + new_section + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    args = ap.parse_args()
    t = args.ticker.upper()

    md_path = Path(f"outputs/{t}_SUPER_Memo.md")
    if not md_path.exists():
        raise SystemExit(f"Missing {md_path}. Run build_super_memo.py first.")

    row = load_comps_row(t)
    md = md_path.read_text(encoding="utf-8")
    new_section = build_linked_cheatsheet(t, row)
    out = replace_section(md, new_section)
    md_path.write_text(out, encoding="utf-8")
    print(f"DONE ✅ Linked cheat-sheet written into {md_path}")

if __name__ == "__main__":
    main()
