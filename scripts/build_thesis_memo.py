from pathlib import Path
import json
from typing import Dict, Any
import pandas as pd
from datetime import datetime
from docx import Document

BASE = Path(__file__).resolve().parents[1]
DATA_PROCESSED = BASE / "data" / "processed"
OUTPUTS = BASE / "outputs"
EXPORT = BASE / "export"
THESES = BASE / "theses"

OUTPUTS.mkdir(exist_ok=True)
EXPORT.mkdir(exist_ok=True)

# ---------------- helpers ----------------

def _safe_read_csv(p):
    try:
        return pd.read_csv(p)
    except Exception:
        return None

def _first_row_as_dict(df, col, val):
    if df is None or df.empty or col not in df.columns:
        return {}
    r = df[df[col].astype(str).str.upper() == val.upper()]
    if r.empty:
        return {}
    return r.iloc[0].to_dict()

def _risk_metric_key(tag, window):
    return f"risk_{tag.lower()}_neg_{window}"

# ---------------- metric lookup ----------------

def _build_metric_lookup(summary, proxy_df, comps_df, risk_df, ticker):

    out = {}

    fundamentals = _safe_read_csv(DATA_PROCESSED / "fundamentals_annual_history.csv")
    if fundamentals is not None and not fundamentals.empty:
        fundamentals = fundamentals.sort_values("period_end")
        last = fundamentals.iloc[-1]

        out["latest_revenue_yoy_pct"] = last.get("revenue_yoy_pct")
        out["latest_free_cash_flow"] = last.get("free_cash_flow")
        out["latest_fcf_margin_pct"] = last.get("fcf_margin_pct")

    proxy = _first_row_as_dict(proxy_df, "ticker", ticker)
    out["news_shock_30d"] = proxy.get("shock_30d")

    comps = _first_row_as_dict(comps_df, "ticker", ticker)
    fy = comps.get("fcf_yield")
    if fy is not None:
        out["fcf_yield_pct"] = float(fy) * 100

    risk = risk_df[risk_df["ticker"] == ticker] if risk_df is not None else pd.DataFrame()
    for _, r in risk.iterrows():
        tag = r["risk_tag"]
        out[_risk_metric_key(tag, "30d")] = r["neg_count_30d"]

    return out

# ---------------- thesis eval ----------------

def eval_claim(val, op, thresh):
    try:
        v = float(val)
        t = float(thresh)
    except Exception:
        return None

    if op == ">=": return v >= t
    if op == ">": return v > t
    if op == "<=": return v <= t
    if op == "<": return v < t
    return None

# ---------------- main ----------------

def main():

    ticker = "UBER"

    thesis = json.load(open(THESES / f"{ticker}_thesis.json"))

    summary = json.load(open(OUTPUTS / "decision_summary.json"))

    proxy = _safe_read_csv(DATA_PROCESSED / "news_sentiment_proxy.csv")
    comps = _safe_read_csv(DATA_PROCESSED / "comps_snapshot.csv")
    risk = _safe_read_csv(DATA_PROCESSED / "news_risk_dashboard.csv")

    metrics = _build_metric_lookup(summary, proxy, comps, risk, ticker)

    total_w = 0
    pass_w = 0
    rows = []

    for c in thesis["claims"]:
        total_w += c["weight"]
        actual = metrics.get(c["metric"])
        ok = eval_claim(actual, c["operator"], c["threshold"])

        status = "UNKNOWN"
        if ok is True:
            status = "PASS"
            pass_w += c["weight"]
        elif ok is False:
            status = "FAIL"

        rows.append((status, c["statement"], c["metric"], actual))

    support = round(100 * pass_w / total_w, 1)

    md = []
    md.append(f"# Thesis Validation Memo — {ticker}")
    md.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n")

    md.append("## Thesis being tested")
    md.append(f"**{thesis['name']}**")
    md.append(thesis["description"] + "\n")

    md.append("## Result")
    md.append(f"- Model rating: **{summary['rating']}** (score {summary['score']}/100)")
    md.append(f"- Thesis support: **{support}%**\n")

    md.append("## Claims checklist\n")

    for r in rows:
        md.append(f"- **{r[0]}** — {r[1]}  \n  Metric `{r[2]}` → **{r[3]}**")

    out_md = OUTPUTS / f"thesis_validation_{ticker}.md"
    out_md.write_text("\n".join(md))

    # Word doc
    doc = Document()
    for l in md:
        doc.add_paragraph(l)
    doc.save(EXPORT / f"{ticker}_Thesis_Memo.docx")

    print("DONE ✅ Thesis memo created:")
    print(out_md)
    print(EXPORT / f"{ticker}_Thesis_Memo.docx")

if __name__ == "__main__":
    main()
