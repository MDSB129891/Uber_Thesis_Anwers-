from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


ROOT = Path(__file__).resolve().parents[1]
THESIS_DIR = ROOT / "theses"
OUTPUTS = ROOT / "outputs"
EXPORT = ROOT / "export"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.strip().lower())
    s = re.sub(r"\s+", "_", s)
    return s[:60] if s else "thesis"


@dataclass
class Claim:
    id: str
    statement: str
    metric: str
    operator: str
    threshold: float | int
    weight: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "weight": self.weight,
        }


def build_default_claims(thesis_text: str) -> List[Claim]:
    """
    Heuristic: always include core fundamentals + valuation + news sanity.
    Then add keyword-triggered claims (EV, pricing power, margins, regulation, etc.).
    """
    t = (thesis_text or "").lower()

    claims: List[Claim] = [
        Claim(
            id="rev_growth",
            statement="Revenue is still growing at a healthy pace",
            metric="latest_revenue_yoy_pct",
            operator=">=",
            threshold=5,
            weight=2,
        ),
        Claim(
            id="fcf_positive",
            statement="Free cash flow is positive",
            metric="latest_free_cash_flow",
            operator=">",
            threshold=0,
            weight=3,
        ),
        Claim(
            id="fcf_margin_ok",
            statement="Free cash flow margin is solid",
            metric="latest_fcf_margin_pct",
            operator=">=",
            threshold=5,
            weight=2,
        ),
        Claim(
            id="valuation_ok",
            statement="Valuation is not expensive versus cash (FCF yield is decent)",
            metric="fcf_yield_pct",
            operator=">=",
            threshold=2.0,
            weight=2,
        ),
        Claim(
            id="news_not_crisis",
            statement="Recent news shock is not severe (not a headline crisis)",
            metric="news_shock_30d",
            operator=">=",
            threshold=-20,
            weight=1,
        ),
    ]

    # Keyword-triggered “thesis flavor”
    if any(k in t for k in ["ev", "electric", "battery", "gigafactory", "charging"]):
        claims += [
            Claim(
                id="ev_story_not_headline_crisis",
                statement="EV narrative is not dominated by negative headlines recently",
                metric="risk_regulatory_neg_30d",
                operator="<=",
                threshold=10,
                weight=1,
            )
        ]

    if any(k in t for k in ["regulation", "antitrust", "sec", "doj", "ftc"]):
        claims += [
            Claim(
                id="reg_not_spiking",
                statement="Regulatory negatives are not spiking recently",
                metric="risk_regulatory_neg_30d",
                operator="<=",
                threshold=5,
                weight=2,
            )
        ]

    if any(k in t for k in ["labor", "union", "strike", "wage"]):
        claims += [
            Claim(
                id="labor_not_spiking",
                statement="Labor risk is not spiking recently",
                metric="risk_labor_neg_30d",
                operator="<=",
                threshold=5,
                weight=2,
            )
        ]

    if any(k in t for k in ["insurance", "claims", "accident", "safety"]):
        claims += [
            Claim(
                id="insurance_not_spiking",
                statement="Insurance risk is not spiking recently",
                metric="risk_insurance_neg_30d",
                operator="<=",
                threshold=5,
                weight=2,
            )
        ]

    # Keep it sane
    # Deduplicate by id
    seen = set()
    out = []
    for c in claims:
        if c.id in seen:
            continue
        seen.add(c.id)
        out.append(c)
    return out


def write_thesis_file(ticker: str, thesis_text: str) -> Path:
    THESIS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{ticker}: {thesis_text.strip()[:80]}".strip()
    thesis = {
        "name": name,
        "ticker": ticker,
        "description": thesis_text.strip(),
        "claims": [c.to_dict() for c in build_default_claims(thesis_text)],
    }
    fp = THESIS_DIR / f"{ticker}_{slugify(thesis_text)}.json"
    fp.write_text(json.dumps(thesis, indent=2), encoding="utf-8")
    return fp


def render_command_center(ticker: str, thesis_path: str) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    # Files we expect from your pipeline
    paths = {
        "Decision dashboard (one-page hub)": f"outputs/decision_dashboard_{ticker}.html",
        "Full memo (PDF)": f"export/{ticker}_Full_Investment_Memo.pdf",
        "Full memo (DOCX)": f"export/{ticker}_Full_Investment_Memo.docx",
        "Clickpack (news links)": f"outputs/news_clickpack_{ticker}.html",
        "Claim evidence (thesis stress test)": f"outputs/claim_evidence_{ticker}.html",
        "Veracity / confidence JSON": f"outputs/veracity_{ticker}.json",
        "Alerts (red lines)": f"outputs/alerts_{ticker}.json",
        "Hybrid signals JSON": f"outputs/hybrid_signals_{ticker}.json",
        "Unified news CSV": "data/processed/news_unified.csv",
        "Clean news CSV": "data/processed/news_unified_clean.csv",
        "News risk dashboard CSV": "data/processed/news_risk_dashboard.csv",
        "Fundamentals annual history CSV": "data/processed/fundamentals_annual_history.csv",
    }

    def li(label: str, rel: str) -> str:
        p = ROOT / rel
        ok = p.exists()
        badge = "✅" if ok else "⚠️"
        # Use relative links from outputs/ to keep it simple
        href = "../" + rel
        return f'<li>{badge} <a href="{href}">{label}</a> <code>{rel}</code></li>'

    html = [
        "<!doctype html>",
        "<html><head><meta charset='utf-8'/>",
        f"<title>GALACTUS Command Center — {ticker}</title>",
        "<style>body{font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width: 900px; margin: 24px auto; padding: 0 12px;} code{background:#f3f3f3;padding:2px 6px;border-radius:6px;} .card{border:1px solid #ddd;border-radius:14px;padding:14px 16px;margin:12px 0;} h1{margin:0 0 6px 0;} ul{line-height:1.7;}</style>",
        "</head><body>",
        f"<h1>🪐 GALACTUS Command Center — {ticker}</h1>",
        f"<p><b>Generated:</b> {utc_now()}</p>",
        "<div class='card'>",
        "<h2>1) What you typed</h2>",
        f"<p><b>Ticker:</b> <code>{ticker}</code></p>",
        f"<p><b>Thesis file:</b> <code>{thesis_path}</code></p>",
        "</div>",
        "<div class='card'>",
        "<h2>2) What to open (in order)</h2>",
        "<ol>",
        "<li><b>Decision dashboard</b> (the hub)</li>",
        "<li><b>Full memo PDF</b> (novice-friendly explanation)</li>",
        "<li><b>Claim evidence</b> (why thesis claims pass/fail + links)</li>",
        "<li><b>Clickpack</b> (raw headlines so you can verify)</li>",
        "</ol>",
        "</div>",
        "<div class='card'>",
        "<h2>3) All important artifacts</h2>",
        "<ul>",
        *[li(k, v) for k, v in paths.items()],
        "</ul>",
        "</div>",
        "<div class='card'>",
        "<h2>4) Plain-English cheat sheet</h2>",
        "<ul>",
        "<li><b>Score</b>: 0–100 overall signal from buckets (cash, growth, valuation, quality, balance/risk).</li>",
        "<li><b>Thesis support</b>: % of weighted claims that passed (your beliefs vs reality).</li>",
        "<li><b>Confidence</b>: how trustworthy/varied the evidence sources are (single-source bias lowers it).</li>",
        "<li><b>Red flags</b>: things that can break the story fast (declining revenue, bad news shock, repeated risk tags).</li>",
        "</ul>",
        "</div>",
        "</body></html>",
    ]

    fp = OUTPUTS / f"galactus_{ticker}.html"
    fp.write_text("\n".join(html), encoding="utf-8")
    return fp


def run_snap(ticker: str, peers: str, thesis_file: str) -> None:
    env = dict(os.environ)
    env["TICKER"] = ticker
    env["PEERS"] = peers
    env["THESIS"] = thesis_file
    env["MODE"] = env.get("MODE", "hybrid")

    # Your run_snap.sh already works; we just set env vars so you never retype.
    subprocess.check_call(["./scripts/run_snap.sh"], cwd=str(ROOT), env=env)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True, help="e.g. GM")
    ap.add_argument("--thesis", required=True, help="Natural language thesis text")
    ap.add_argument("--peers", default="", help="Comma-separated peers, e.g. F,TM. Leave blank to let your pipeline choose defaults.")
    args = ap.parse_args()

    ticker = args.ticker.upper().strip()
    thesis_text = args.thesis.strip()

    thesis_fp = write_thesis_file(ticker, thesis_text)

    # peers: if blank, keep existing defaults (your run_snap.sh will handle)
    peers = args.peers.strip()

    print(f"🪐 GALACTUS RUN — {ticker}")
    print(f"Thesis: {thesis_text}")
    print(f"Generated thesis JSON: {thesis_fp}")

    run_snap(ticker, peers, str(thesis_fp))

    cc = render_command_center(ticker, str(thesis_fp))
    print(f"DONE ✅ Command center: {cc}")
    print(f"Open it: open {cc}")


if __name__ == "__main__":
    main()
