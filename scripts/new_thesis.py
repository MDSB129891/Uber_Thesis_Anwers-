#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THESES = ROOT / "theses"
THESES.mkdir(parents=True, exist_ok=True)

DEFAULT_METRICS = [
    ("latest_revenue_yoy_pct", ">=", 10, 2, "Revenue is still growing at a healthy pace"),
    ("latest_free_cash_flow", ">", 0, 3, "Free cash flow is positive"),
    ("latest_fcf_margin_pct", ">=", 10, 2, "Free cash flow margin is solid"),
    ("fcf_yield_pct", ">=", 3, 2, "Valuation is not expensive versus cash (FCF yield is decent)"),
    ("news_shock_30d", ">=", -15, 1, "Recent news shock is not severe (not a headline crisis)"),
    ("risk_insurance_neg_30d", "<=", 3, 1, "Insurance risk is not spiking recently"),
    ("risk_regulatory_neg_30d", "<=", 3, 1, "Regulatory risk is not spiking recently"),
    ("risk_labor_neg_30d", "<=", 3, 1, "Labor risk is not spiking recently"),
]

def ask(prompt: str, default: str = "") -> str:
    s = input(f"{prompt} [{default}]: ").strip()
    return s or default

def ask_int(prompt: str, default: int) -> int:
    s = ask(prompt, str(default))
    try:
        return int(float(s))
    except Exception:
        return default

def ask_float(prompt: str, default: float) -> float:
    s = ask(prompt, str(default))
    try:
        return float(s)
    except Exception:
        return default

def main():
    ticker = ask("Ticker", "UBER").upper()
    name = ask("Thesis name (headline)", f"{ticker}: Thesis")
    desc = ask("One-paragraph thesis description", f"{ticker} should generate cash while valuation stays reasonable; risks aren't escalating.")

    claims = []
    print("\nWe'll build claims (rules). Press Enter to accept defaults.\n")
    use_defaults = ask("Use default starter claims? (y/n)", "y").lower().startswith("y")
    if use_defaults:
        for i, (metric, op, thr, w, statement) in enumerate(DEFAULT_METRICS, 1):
            keep = ask(f"Keep claim #{i}: {statement}? (y/n)", "y").lower().startswith("y")
            if not keep:
                continue
            thr2 = ask_float(f"  Threshold for {metric} ({op})", float(thr))
            w2 = ask_int("  Weight (importance)", int(w))
            claims.append({"id": f"c{i}", "statement": statement, "metric": metric, "operator": op, "threshold": thr2, "weight": w2})

    while True:
        more = ask("\nAdd another custom claim? (y/n)", "n").lower().startswith("y")
        if not more:
            break
        statement = ask("  Claim statement (plain English)", "Some claim")
        metric = ask("  Metric key (e.g. latest_revenue_yoy_pct)", "latest_revenue_yoy_pct")
        op = ask("  Operator (>=, >, <=, <)", ">=")
        thr = ask_float("  Threshold", 10.0)
        w = ask_int("  Weight (importance)", 1)
        claims.append({"id": statement[:24].lower().replace(" ", "_"), "statement": statement, "metric": metric, "operator": op, "threshold": thr, "weight": w})

    thesis = {"name": name, "ticker": ticker, "description": desc, "claims": claims}

    out = THESES / f"{ticker}_thesis_custom.json"
    out.write_text(json.dumps(thesis, indent=2), encoding="utf-8")

    print("\nDONE ✅ Thesis created:")
    print(f"- {out}\n")
    print("Run it like:")
    print(f"python3 scripts/build_investment_memo.py --ticker {ticker} --thesis {out}")

if __name__ == "__main__":
    main()
