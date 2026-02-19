#!/usr/bin/env python3
from __future__ import annotations

from typing import Dict, Any, List

def _top_weak_buckets(bucket_scores: Dict[str, Any], n: int = 2) -> List[str]:
    items = []
    for k, v in (bucket_scores or {}).items():
        try:
            items.append((k, float(v)))
        except Exception:
            continue
    items.sort(key=lambda x: x[1])  # weakest first
    return [k for k, _ in items[:n]]

def build_verdict(decision: Dict[str, Any], proxy_row: Dict[str, Any] | None = None) -> str:
    rating = str(decision.get("rating", "N/A")).upper()
    score = decision.get("score", "N/A")
    red_flags = decision.get("red_flags") or []
    bucket = decision.get("bucket_scores") or {}

    weak = _top_weak_buckets(bucket, 2)
    weak_txt = ", ".join([w.replace("_", " ") for w in weak]) if weak else "risk/valuation"

    shock_7d = None
    try:
        if proxy_row:
            shock_7d = proxy_row.get("shock_7d")
    except Exception:
        shock_7d = None

    # Core templates
    if rating == "BUY":
        base = f"Verdict: BUY (score {score}/100) — fundamentals/quality are supportive, but watch {weak_txt}."
    elif rating == "HOLD":
        base = f"Verdict: HOLD (score {score}/100) — mixed signals; strongest areas offset by weaker {weak_txt}."
    elif rating == "AVOID":
        base = f"Verdict: AVOID (score {score}/100) — the current setup looks fragile, mainly due to weak {weak_txt}."
    else:
        base = f"Verdict: {rating} (score {score}/100)."

    # Add red flags if present
    if red_flags:
        add = " Key concerns: " + "; ".join(red_flags[:3]) + "."
    else:
        add = ""

    # Optional news shock note
    try:
        if shock_7d is not None and float(shock_7d) <= -20:
            add += " Headlines are unusually negative in the last 7 days (news shock is severe)."
    except Exception:
        pass

    return (base + add).strip()
