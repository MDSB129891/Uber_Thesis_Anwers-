from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class NewsItem:
    published_at: str               # ISO string
    ticker: str
    title: str
    source: str                     # gdelt / sec / ir_rss / fmp / ...
    url: str
    summary: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    # Filled later by scoring
    risk_tag: Optional[str] = None  # LABOR / INSURANCE / REGULATORY / SAFETY / COMPETITION / MACRO / FINANCIAL / OTHER
    impact_score: Optional[int] = None  # -3..+3
    sentiment: Optional[float] = None
    dedupe_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
