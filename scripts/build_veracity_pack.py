#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
EXPORT = ROOT / "export"

OUTPUTS.mkdir(parents=True, exist_ok=True)

DEFAULT_TICKER = "UBER"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def safe_read_whitelist(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        df = pd.read_csv(path)
        cols = [c.lower() for c in df.columns]
        if "domain" in cols:
            return [str(x).strip().lower() for x in df[df.columns[cols.index("domain")]].dropna().tolist()]
        if len(df.columns) == 1:
            return [str(x).strip().lower() for x in df[df.columns[0]].dropna().tolist()]
        return []
    except Exception:
        return []


def domain_of(url: str) -> str:
    try:
        u = urlparse(str(url))
        d = (u.netloc or "").lower()
        return d.replace("www.", "")
    except Exception:
        return ""


def coerce_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, str) and x.strip() == "":
            return None
        return float(x)
    except Exception:
        return None


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def parse_dt(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    try:
        ss = str(s).strip()
        if not ss:
            return None
        dt = datetime.fromisoformat(ss.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def build_confidence_breakdown(df: pd.DataFrame, whitelist_domains: List[str]) -> Tuple[int, dict]:
    if df.empty:
        return 0, {"reason": "no evidence rows"}

    n = len(df)

    url_cov = float(df["url"].notna().mean()) if "url" in df.columns else 0.0

    sources = df["source"].fillna("unknown").astype(str).str.lower() if "source" in df.columns else pd.Series(["unknown"] * n)
    sc = Counter(sources)
    top_source, top_count = sc.most_common(1)[0]
    top_share = top_count / n

    domains = df["url"].fillna("").apply(domain_of) if "url" in df.columns else pd.Series([""] * n)
    uniq_domains = len(set([d for d in domains.tolist() if d]))
    domain_diversity = uniq_domains / max(1, n)

    sec_share = float((sources == "sec").mean())

    wl = set([d.strip().lower() for d in whitelist_domains if d.strip()])
    wl_hits = domains.apply(lambda d: 1 if d in wl else 0) if wl else pd.Series([0] * n)
    wl_share = float(wl_hits.mean())

    if "published_at" in df.columns:
        dts = df["published_at"].apply(parse_dt)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_share = float(dts.apply(lambda x: 1 if (x and x >= cutoff) else 0).mean())
    else:
        recent_share = 0.0

    if "title" in df.columns:
        titles = df["title"].fillna("").astype(str).str.lower().str.strip()
        dup_ratio = 1.0 - (titles.nunique() / max(1, n))
    else:
        dup_ratio = 0.0

    score = 100.0

    score -= (1.0 - url_cov) * 60.0

    if top_share > 0.70:
        score -= (top_share - 0.70) * 120.0

    if uniq_domains < 10:
        score -= 8.0
    score += clamp(domain_diversity * 40.0, 0.0, 12.0)

    score += clamp(sec_share * 60.0, 0.0, 18.0)

    score += clamp(wl_share * 80.0, 0.0, 20.0)

    score += clamp(recent_share * 20.0, 0.0, 8.0)

    score -= clamp(dup_ratio * 25.0, 0.0, 10.0)

    score = clamp(score, 0.0, 100.0)

    breakdown = {
        "rows": n,
        "url_coverage": round(url_cov, 3),
        "top_source": top_source,
        "top_source_share": round(top_share, 3),
        "unique_domains": uniq_domains,
        "sec_share": round(sec_share, 3),
        "whitelist_share": round(wl_share, 3),
        "recent_share_7d": round(recent_share, 3),
        "dup_ratio_titles": round(dup_ratio, 3),
        "notes": [
            "Confidence is evidence-quality + cross-checkability (not stock performance).",
            "Single-source dominance lowers confidence. SEC + reputable domains raise it.",
        ],
    }
    return int(round(score)), breakdown


def pick_must_click(df: pd.DataFrame, k: int = 10) -> List[dict]:
    if df.empty:
        return []

    d = df.copy()

    if "impact_score" not in d.columns:
        d["impact_score"] = None
    d["impact_score_num"] = d["impact_score"].apply(coerce_float)

    if "published_at" in d.columns:
        d["dt"] = d["published_at"].apply(parse_dt)
    else:
        d["dt"] = None

    d["rank_key"] = d["impact_score_num"].apply(lambda x: x if x is not None else 0.0)

    d = d.sort_values(by=["rank_key", "dt"], ascending=[True, False], na_position="last")

    out = []
    for _, r in d.head(k).iterrows():
        out.append({
            "published_at": r.get("published_at"),
            "title": r.get("title"),
            "source": r.get("source"),
            "risk_tag": r.get("risk_tag"),
            "impact_score": r.get("impact_score"),
            "url": r.get("url"),
        })
    return out


def write_clickpack_html(ticker: str, must_click: List[dict], path: Path) -> None:
    rows = []
    for it in must_click:
        title = (it.get("title") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        url = it.get("url") or ""
        src = it.get("source") or ""
        tag = it.get("risk_tag") or ""
        imp = it.get("impact_score")
        dt = it.get("published_at") or ""
        link = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>' if url else title
        rows.append(f"<tr><td>{dt}</td><td>{src}</td><td>{tag}</td><td>{imp}</td><td>{link}</td></tr>")

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{ticker} — News Click Pack</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; padding: 24px; }}
h1 {{ margin-bottom: 6px; }}
small {{ color: #666; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
</style>
</head>
<body>
<h1>{ticker} — Click Pack (Top headlines to verify)</h1>
<small>Generated: {utc_now_iso()} — Click the most negative headlines first. If the same risk repeats, treat it more seriously.</small>

<h2>Top {len(must_click)} must-click items</h2>
<table>
<tr><th>Published</th><th>Source</th><th>Risk</th><th>Impact</th><th>Headline</th></tr>
{''.join(rows)}
</table>

<p style="margin-top:18px;color:#666;">
Tip: If most items come from one source, confirm with at least one other outlet or SEC filings before trusting the story.
</p>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main():
    ticker = DEFAULT_TICKER

    unified = safe_read_csv(DATA_PROCESSED / "news_unified.csv")
    if unified.empty:
        print("No news_unified.csv found or it's empty.")
        return

    if "ticker" in unified.columns:
        df = unified[unified["ticker"].astype(str).str.upper() == ticker.upper()].copy()
    else:
        df = unified.copy()

    whitelist = safe_read_whitelist(EXPORT / "source_whitelist.csv")

    confidence, breakdown = build_confidence_breakdown(df, whitelist)
    must_click = pick_must_click(df, k=10)

    out = {
        "ticker": ticker,
        "generated_utc": utc_now_iso(),
        "confidence_score": confidence,
        "breakdown": breakdown,
        "must_click": must_click,
    }

    out_path = OUTPUTS / f"veracity_{ticker}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    html_path = OUTPUTS / f"news_clickpack_{ticker}.html"
    write_clickpack_html(ticker, must_click, html_path)

    print("DONE ✅ Veracity pack created:")
    print(f"- {out_path}")
    print(f"- {html_path}")


if __name__ == "__main__":
    main()
