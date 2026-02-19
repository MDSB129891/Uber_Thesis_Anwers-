import argparse, json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def load_news_risk(ticker: str):
    t = ticker.upper().strip()

    shock_30d = None
    shock_7d = None

    labor_neg_30d = 0
    regulatory_neg_30d = 0
    insurance_neg_30d = 0

    # 1) Sentiment proxy has the headline shock numbers
    p_proxy = ROOT / "data/processed/news_sentiment_proxy.csv"
    if p_proxy.exists():
        df = pd.read_csv(p_proxy)
        if "ticker" in df.columns:
            df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
            r = df[df["ticker"] == t]
            if len(r):
                row = r.iloc[0].to_dict()
                shock_30d = row.get("shock_30d", None)
                shock_7d  = row.get("shock_7d", None)

    # 2) Risk dashboard has per-tag negative counts
    p_risk = ROOT / "data/processed/news_risk_dashboard.csv"
    if p_risk.exists():
        df = pd.read_csv(p_risk)
        if "ticker" in df.columns:
            df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
            r = df[df["ticker"] == t]

            # Map your tags into your memo buckets
            # (If a tag isn't present, treat as 0 — not N/A)
            if len(r):
                by_tag = {str(k).upper(): float(v) for k, v in r.groupby("risk_tag")["neg_count_30d"].sum().to_dict().items()}
                insurance_neg_30d   = int(by_tag.get("INSURANCE", 0))
                regulatory_neg_30d  = int(by_tag.get("REGULATORY", 0))
                labor_neg_30d       = int(by_tag.get("LABOR", 0))

    return {
        "ticker": t,
        "news_shock_30d": shock_30d,
        "news_shock_7d": shock_7d,
        "risk_labor_neg_30d": labor_neg_30d,
        "risk_regulatory_neg_30d": regulatory_neg_30d,
        "risk_insurance_neg_30d": insurance_neg_30d,
        "source": {
            "sentiment_proxy": "data/processed/news_sentiment_proxy.csv",
            "risk_dashboard": "data/processed/news_risk_dashboard.csv",
        }
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    args = ap.parse_args()

    out = load_news_risk(args.ticker)
    out_path = ROOT / "outputs" / f"news_risk_summary_{out['ticker']}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("DONE ✅ wrote:", out_path)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
