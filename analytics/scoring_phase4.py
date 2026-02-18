from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd


@dataclass
class Phase4Paths:
    root: Path
    processed: Path
    outputs: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        # make pandas / numpy types json-safe
        try:
            import numpy as np
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
        except Exception:
            pass
        if hasattr(o, "item"):
            try:
                return o.item()
            except Exception:
                pass
        return str(o)

    path.write_text(json.dumps(obj, indent=2, default=_default), encoding="utf-8")


def _coerce_num(x, default=None):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def _latest_row(df: pd.DataFrame, date_col: str) -> Optional[pd.Series]:
    if df.empty or date_col not in df.columns:
        return None
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col]).sort_values(date_col)
    if d.empty:
        return None
    return d.iloc[-1]


def _trend_slope(series: pd.Series) -> float:
    """Very simple slope proxy; positive = improving."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 3:
        return 0.0
    return float((s.iloc[-1] - s.iloc[0]) / max(1, (len(s) - 1)))


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        u = str(url or "").strip()
        if not u.startswith("http"):
            return ""
        netloc = urlparse(u).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _load_whitelist_domains(root: Path) -> set:
    """
    Reads export/source_whitelist.csv if present.
    Expected columns could be: domain, tier, allow, notes (we're flexible)
    """
    wl_path = root / "export" / "source_whitelist.csv"
    if not wl_path.exists():
        return set()
    try:
        df = pd.read_csv(wl_path)
    except Exception:
        return set()

    # Accept "domain" or "source" column
    col = None
    for c in ["domain", "source", "host"]:
        if c in df.columns:
            col = c
            break
    if col is None:
        return set()

    domains = set()
    for x in df[col].astype(str).fillna("").tolist():
        d = x.strip().lower()
        if d.startswith("www."):
            d = d[4:]
        if d:
            domains.add(d)
    return domains


def compute_data_completeness(inputs: Dict[str, Any]) -> Tuple[int, List[str]]:
    missing: List[str] = []

    required = [
        ("comps_snapshot", inputs.get("comps_snapshot")),
        ("fundamentals_annual_history", inputs.get("fundamentals_annual_history")),
        ("news_unified", inputs.get("news_unified")),
        ("news_sentiment_proxy", inputs.get("news_sentiment_proxy")),
        ("news_risk_dashboard", inputs.get("news_risk_dashboard")),
    ]

    total_checks = 0
    good_checks = 0

    for name, df in required:
        total_checks += 1
        if isinstance(df, pd.DataFrame) and not df.empty:
            good_checks += 1
        else:
            missing.append(f"Missing or empty: {name}")

    ticker = str(inputs.get("ticker", "")).upper()
    comps = inputs.get("comps_snapshot")
    if isinstance(comps, pd.DataFrame) and not comps.empty and "ticker" in comps.columns:
        row = comps[comps["ticker"].astype(str).str.upper() == ticker]
        total_checks += 1
        if not row.empty:
            good_checks += 1
        else:
            missing.append(f"Ticker not present in comps_snapshot: {ticker}")

    score = int(round((good_checks / max(1, total_checks)) * 100))
    return score, missing


def compute_confidence_veracity(
    root: Path,
    ticker: str,
    news_unified: pd.DataFrame,
) -> Tuple[int, List[str], Dict[str, Any]]:
    """
    0–100 score measuring how easy the evidence is to verify.
    Not a forecast. Not “truth”. Just “can a human click and validate quickly?”
    """
    reasons: List[str] = []
    meta: Dict[str, Any] = {}

    if news_unified is None or news_unified.empty:
        return 0, ["No news evidence rows found (news_unified.csv empty)."], {"source_counts": {}}

    df = news_unified.copy()
    df["ticker"] = df.get("ticker", "").astype(str).str.upper()
    df = df[df["ticker"] == ticker.upper()].copy()
    if df.empty:
        return 0, [f"No news rows for {ticker} in news_unified.csv."], {"source_counts": {}}

    # Normalize fields
    df["source"] = df.get("source", "unknown").astype(str).str.lower()
    df["url"] = df.get("url", "").astype(str)
    df["domain"] = df["url"].apply(_extract_domain)

    # Source mix
    source_counts = df["source"].value_counts(dropna=False).to_dict()
    total = int(df.shape[0])
    meta["total_rows"] = total
    meta["source_counts"] = {k: int(v) for k, v in source_counts.items()}

    # URL coverage
    has_url = df["url"].str.startswith("http").sum()
    url_ratio = float(has_url / max(1, total))
    meta["url_ratio"] = url_ratio

    # Whitelist coverage
    whitelist = _load_whitelist_domains(root)
    meta["whitelist_loaded"] = bool(whitelist)
    if whitelist:
        top_tier_hits = df["domain"].isin(whitelist).sum()
        top_tier_ratio = float(top_tier_hits / max(1, total))
    else:
        top_tier_hits = 0
        top_tier_ratio = 0.0
    meta["top_tier_hits"] = int(top_tier_hits)
    meta["top_tier_ratio"] = top_tier_ratio

    # SEC presence (high veracity)
    sec_rows = int((df["source"] == "sec").sum())
    meta["sec_rows"] = sec_rows
    sec_ratio = float(sec_rows / max(1, total))

    # Single-source bias (bad for confidence, even if big quantity)
    largest_source = max(source_counts.items(), key=lambda kv: kv[1])[0]
    largest_share = float(source_counts[largest_source] / max(1, total))
    meta["largest_source"] = largest_source
    meta["largest_source_share"] = largest_share

    # Score components (simple + explainable)
    # Base: start at 20 for having any evidence
    score = 20

    # Clickability
    if url_ratio >= 0.90:
        score += 25
        reasons.append("Most evidence rows have clickable URLs (easy to verify).")
    elif url_ratio >= 0.60:
        score += 18
        reasons.append("Many evidence rows have clickable URLs.")
    elif url_ratio >= 0.30:
        score += 10
        reasons.append("Some evidence rows have URLs, but many are not directly verifiable by click.")
    else:
        score += 0
        reasons.append("Few evidence rows have URLs (hard to verify quickly).")

    # High-trust sources
    if sec_ratio >= 0.05:
        score += 15
        reasons.append("SEC filings included (high-veracity sources).")
    elif sec_rows > 0:
        score += 10
        reasons.append("Some SEC filings included.")

    # Top-tier domains (if whitelist exists)
    if whitelist:
        if top_tier_ratio >= 0.30:
            score += 20
            reasons.append("A meaningful share of articles come from your top-tier domain whitelist.")
        elif top_tier_ratio >= 0.10:
            score += 12
            reasons.append("Some articles come from your top-tier domain whitelist.")
        else:
            score += 4
            reasons.append("Few articles match your top-tier whitelist (not necessarily bad, but weaker verifiability).")
    else:
        reasons.append("No whitelist loaded; confidence uses source mix + URL coverage only.")

    # Diversity penalty
    if largest_share >= 0.90:
        score -= 20
        reasons.append(f"Single-source bias: ~{largest_share*100:.0f}% from {largest_source}.")
    elif largest_share >= 0.75:
        score -= 10
        reasons.append(f"Source concentration: ~{largest_share*100:.0f}% from {largest_source}.")
    else:
        score += 5
        reasons.append("Evidence is reasonably diversified across sources.")

    # Cap and floor
    score = int(max(0, min(100, round(score))))

    # Add a compact summary line (nice for humans)
    reasons.insert(
        0,
        f"Evidence rows={total}, URL coverage={url_ratio*100:.0f}%, top source={largest_source} ({largest_share*100:.0f}%)."
    )

    return score, reasons, meta


def compute_red_flags(
    ticker: str,
    annual_hist: pd.DataFrame,
    comps_row: Optional[pd.Series],
    news_proxy_row: Optional[pd.Series],
    risk_dash: pd.DataFrame,
) -> List[dict]:
    flags: List[dict] = []
    t = ticker.upper()

    if not annual_hist.empty:
        h = annual_hist.copy()
        if "period_end" in h.columns:
            h["period_end"] = pd.to_datetime(h["period_end"], errors="coerce")
            h = h.dropna(subset=["period_end"]).sort_values("period_end")

        if "free_cash_flow" in h.columns:
            fcf = pd.to_numeric(h["free_cash_flow"], errors="coerce").dropna()
            if len(fcf) >= 4:
                base = fcf.abs().mean()
                vol = float(fcf.std() / base) if base and base > 0 else 0.0
                if vol >= 0.8:
                    flags.append({
                        "id": "FCF_VOLATILE",
                        "severity": "MED",
                        "title": "Free cash flow is volatile",
                        "plain_english": "The business generates cash, but it swings a lot year to year.",
                        "why_it_matters": "Volatile cash makes valuation less reliable and increases downside risk in weak years.",
                        "what_to_check": "Read 10-K cash flow discussion: is volatility due to one-time items or structural issues?",
                        "value": {"fcf_volatility_proxy": round(vol, 2)}
                    })
            if len(fcf) >= 2 and fcf.iloc[-1] < 0:
                flags.append({
                    "id": "FCF_NEGATIVE",
                    "severity": "HIGH",
                    "title": "Free cash flow is negative",
                    "plain_english": "The company is burning cash after expenses and investment.",
                    "why_it_matters": "Cash burn forces financing (debt/equity) and raises failure/dilution risk.",
                    "what_to_check": "Is this temporary investment or ongoing operating weakness?",
                    "value": {"latest_fcf": float(fcf.iloc[-1])}
                })

        if "fcf_margin_pct" in h.columns:
            m = pd.to_numeric(h["fcf_margin_pct"], errors="coerce").dropna()
            if len(m) >= 3:
                slope = _trend_slope(m)
                if slope < -1.5:
                    flags.append({
                        "id": "MARGIN_COMPRESS",
                        "severity": "MED",
                        "title": "Cash margin is compressing",
                        "plain_english": "The company is turning a smaller % of sales into free cash than before.",
                        "why_it_matters": "Margin compression often signals rising costs, competition, or pricing pressure.",
                        "what_to_check": "Check unit economics and cost drivers; look for competition or regulatory cost shifts.",
                        "value": {"trend_slope": round(slope, 2)}
                    })

    if comps_row is not None:
        nd_to_fcf = _coerce_num(comps_row.get("net_debt_to_fcf_ttm"), None)
        if nd_to_fcf is not None and nd_to_fcf > 6:
            flags.append({
                "id": "LEVERAGE_HIGH",
                "severity": "HIGH",
                "title": "Leverage looks high vs cash generation",
                "plain_english": f"Net debt is about {nd_to_fcf:.1f} years of free cash flow.",
                "why_it_matters": "High leverage reduces flexibility and increases risk in downturns.",
                "what_to_check": "Debt maturities + interest expense trend; any refinancing risk?",
                "value": {"net_debt_to_fcf_ttm": nd_to_fcf}
            })

        fcf_yield = _coerce_num(comps_row.get("fcf_yield"), None)
        rev_yoy = _coerce_num(comps_row.get("revenue_ttm_yoy_pct"), None)
        if fcf_yield is not None and fcf_yield < 0.01 and (rev_yoy is None or rev_yoy < 10):
            flags.append({
                "id": "VALUATION_STRETCHED",
                "severity": "MED",
                "title": "Valuation may be stretched vs cash",
                "plain_english": "You’re paying a lot for each dollar of free cash flow.",
                "why_it_matters": "Expensive valuations can fall hard if growth slows or margins slip.",
                "what_to_check": "Compare to peers and to the company’s own history; check forward guidance.",
                "value": {"fcf_yield": fcf_yield, "revenue_ttm_yoy_pct": rev_yoy}
            })

    if not risk_dash.empty and "ticker" in risk_dash.columns:
        rd = risk_dash[risk_dash["ticker"].astype(str).str.upper() == t].copy()
        if not rd.empty and "neg_count_30d" in rd.columns:
            hot = rd[pd.to_numeric(rd["neg_count_30d"], errors="coerce").fillna(0) >= 3]
            for _, r in hot.iterrows():
                tag = str(r.get("risk_tag", "OTHER"))
                flags.append({
                    "id": f"RISK_TAG_SPIKE_{tag}",
                    "severity": "MED",
                    "title": f"Repeated negative risk theme: {tag}",
                    "plain_english": f"We saw repeated negatives tagged {tag} over the last 30 days.",
                    "why_it_matters": "Repetition is more important than a single scary headline; it suggests persistence.",
                    "what_to_check": "Open the worst headline(s) under this tag and verify the underlying event.",
                    "value": {"risk_tag": tag, "neg_count_30d": _coerce_num(r.get("neg_count_30d"), 0)}
                })

    if news_proxy_row is not None:
        shock7 = _coerce_num(news_proxy_row.get("shock_7d"), 0)
        shock30 = _coerce_num(news_proxy_row.get("shock_30d"), 0)
        if shock7 is not None and shock7 <= -10:
            flags.append({
                "id": "NEWS_SHOCK_7D",
                "severity": "MED",
                "title": "Severe negative news shock (7 days)",
                "plain_english": "Recent news includes unusually negative/impactful stories.",
                "why_it_matters": "Shocks often reflect real events (lawsuits, regulation, accidents, earnings surprises).",
                "what_to_check": "Verify top 3 negative headlines and whether they’re one-off or repeating.",
                "value": {"shock_7d": shock7, "shock_30d": shock30}
            })

    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    flags.sort(key=lambda x: order.get(x.get("severity", "MED"), 9))
    return flags


def build_scenarios(
    ticker: str,
    comps_row: Optional[pd.Series],
    annual_hist: pd.DataFrame,
) -> dict:
    scenario = {
        "ticker": ticker.upper(),
        "as_of": _utc_now_iso(),
        "method": "FCF projection + implied market cap using target FCF yield",
        "assumptions": {},
        "results": {},
        "notes": [
            "This is a simple range model for context, not a precise valuation.",
            "If growth slows or margins compress, implied value falls; if they improve, implied value rises."
        ],
    }

    if comps_row is None:
        scenario["notes"].append("Missing comps row; scenario model is limited.")
        return scenario

    fcf_ttm = _coerce_num(comps_row.get("fcf_ttm"), None)
    mcap = _coerce_num(comps_row.get("market_cap"), None)
    fcf_yield = _coerce_num(comps_row.get("fcf_yield"), None)

    if fcf_ttm is None or mcap is None or fcf_ttm == 0:
        scenario["notes"].append("Missing FCF TTM or market cap; cannot compute scenarios reliably.")
        return scenario

    base_growth = _coerce_num(comps_row.get("revenue_ttm_yoy_pct"), 10) / 100.0
    base_margin = _coerce_num(comps_row.get("fcf_margin_ttm_pct"), 10) / 100.0

    if not annual_hist.empty and "fcf_margin_pct" in annual_hist.columns:
        last = _latest_row(annual_hist, "period_end")
        if last is not None:
            base_margin = _coerce_num(last.get("fcf_margin_pct"), base_margin * 100) / 100.0

    cur_yield = float(fcf_yield) if fcf_yield is not None and fcf_yield > 0 else float(fcf_ttm / mcap)
    base_target_yield = min(max(cur_yield, 0.02), 0.08)

    scenario["assumptions"] = {
        "fcf_ttm": float(fcf_ttm),
        "market_cap": float(mcap),
        "current_fcf_yield": float(cur_yield),
        "projection_years": 3,
        "base": {
            "fcf_growth": float(min(max(base_growth, 0.03), 0.25)),
            "target_fcf_yield": float(base_target_yield),
        },
        "bull": {
            "fcf_growth": float(min(max(base_growth + 0.05, 0.05), 0.35)),
            "target_fcf_yield": float(max(base_target_yield - 0.01, 0.015)),
        },
        "bear": {
            "fcf_growth": float(max(base_growth - 0.08, -0.05)),
            "target_fcf_yield": float(min(base_target_yield + 0.02, 0.12)),
        },
    }

    def project_fcf(fcf0: float, g: float, years: int) -> float:
        f = fcf0
        for _ in range(years):
            f *= (1.0 + g)
        return f

    years = int(scenario["assumptions"]["projection_years"])

    results = {}
    for name in ("bear", "base", "bull"):
        g = float(scenario["assumptions"][name]["fcf_growth"])
        y = float(scenario["assumptions"][name]["target_fcf_yield"])
        fcfN = project_fcf(float(fcf_ttm), g, years)
        implied_mcap = fcfN / y if y > 0 else None
        upside = ((implied_mcap / mcap) - 1.0) if implied_mcap else None

        results[name] = {
            "projected_fcf": float(fcfN),
            "target_fcf_yield": y,
            "implied_market_cap": float(implied_mcap) if implied_mcap else None,
            "implied_upside_pct": float(upside * 100.0) if upside is not None else None,
        }

    scenario["results"] = results
    return scenario


def enrich_decision_summary(
    root: Path,
    ticker: str,
    outputs_path: Path,
    processed_path: Path,
) -> dict:
    t = ticker.upper()

    decision_summary_path = outputs_path / "decision_summary.json"
    summary = _safe_read_json(decision_summary_path) or {}
    summary["ticker"] = summary.get("ticker", t)
    summary["phase4_upgraded_at"] = _utc_now_iso()

    inputs = {
        "ticker": t,
        "fundamentals_annual_history": _safe_read_csv(processed_path / "fundamentals_annual_history.csv"),
        "fundamentals_quarterly": _safe_read_csv(processed_path / "fundamentals_quarterly.csv"),
        "comps_snapshot": _safe_read_csv(processed_path / "comps_snapshot.csv"),
        "news_unified": _safe_read_csv(processed_path / "news_unified.csv"),
        "news_sentiment_proxy": _safe_read_csv(processed_path / "news_sentiment_proxy.csv"),
        "news_risk_dashboard": _safe_read_csv(processed_path / "news_risk_dashboard.csv"),
        "market_daily": _safe_read_csv(processed_path / "market_daily.csv"),
    }

    completeness_score, completeness_missing = compute_data_completeness(inputs)
    summary["data_completeness_score"] = completeness_score
    summary["data_completeness_missing"] = completeness_missing

    comps = inputs["comps_snapshot"]
    comps_row = None
    if isinstance(comps, pd.DataFrame) and not comps.empty and "ticker" in comps.columns:
        r = comps[comps["ticker"].astype(str).str.upper() == t]
        if not r.empty:
            comps_row = r.iloc[0]

    proxy = inputs["news_sentiment_proxy"]
    proxy_row = None
    if isinstance(proxy, pd.DataFrame) and not proxy.empty and "ticker" in proxy.columns:
        r = proxy[proxy["ticker"].astype(str).str.upper() == t]
        if not r.empty:
            proxy_row = r.iloc[0]

    annual_hist = inputs["fundamentals_annual_history"]
    risk_dash = inputs["news_risk_dashboard"]

    red_flags_structured = compute_red_flags(t, annual_hist, comps_row, proxy_row, risk_dash)
    summary.setdefault("red_flags", [])
    for rf in red_flags_structured:
        s = f"[{rf['severity']}] {rf['title']}"
        if s not in summary["red_flags"]:
            summary["red_flags"].append(s)
    summary["red_flags_structured"] = red_flags_structured

    scenario = build_scenarios(t, comps_row, annual_hist)
    summary["scenario_summary"] = scenario

    # ✅ Confidence / veracity now computed here
    conf_score, conf_reasons, conf_meta = compute_confidence_veracity(
        root=root,
        ticker=t,
        news_unified=inputs["news_unified"],
    )
    summary["confidence_score"] = conf_score
    summary["confidence_reasons"] = conf_reasons
    summary["confidence_meta"] = conf_meta

    # Decision card
    buckets = summary.get("bucket_scores", {}) or {}

    def bucket_light(x: Optional[float]) -> str:
        if x is None:
            return "GRAY"
        try:
            x = float(x)
        except Exception:
            return "GRAY"
        if x >= 17:
            return "GREEN"
        if x >= 13:
            return "YELLOW"
        return "RED"

    decision_card = {
        "ticker": t,
        "as_of": summary.get("as_of", ""),
        "score": summary.get("score", None),
        "rating": summary.get("rating", "N/A"),
        "lights": {k: bucket_light(_coerce_num(v, None)) for k, v in buckets.items()},
        "data_completeness_score": completeness_score,
        "confidence_score": conf_score,
        "top_reasons": summary.get("top_positives", []),
        "top_risks": summary.get("top_risks", []),
        "red_flags": summary.get("red_flags", []),
    }

    audit = {
        "ticker": t,
        "generated_at": _utc_now_iso(),
        "inputs_used": {
            "tables": {
                k: {"rows": int(v.shape[0]), "cols": int(v.shape[1])}
                if isinstance(v, pd.DataFrame) else {}
                for k, v in inputs.items()
            },
        },
        "decision_summary_after_phase4": summary,
        "notes": [
            "Phase 4 reads your pipeline outputs and adds explainability, red flags, scenarios, confidence(veracity), and audit trail.",
            "Confidence score measures how easy it is to verify sources (URLs, top-tier domains, SEC, diversification).",
        ],
    }

    audit_path = outputs_path / f"decision_audit_{t}.json"
    card_path = outputs_path / f"decision_card_{t}.json"
    _safe_write_json(audit_path, audit)
    _safe_write_json(card_path, decision_card)
    _safe_write_json(decision_summary_path, summary)

    return summary
