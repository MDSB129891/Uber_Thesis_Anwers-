from __future__ import annotations

import requests
from typing import List
from datetime import datetime, timedelta, timezone

from ..schema import NewsItem
from ..utils import parse_iso_datetime


def fetch_gdelt(ticker: str, days_back: int = 30, max_items: int = 200) -> List[NewsItem]:
    """
    GDELT 2 DOC API: returns broad coverage.
    Query uses ticker + company name-ish patterns. We keep it simple: just ticker.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)

    # GDELT wants times in YYYYMMDDHHMMSS
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%d%H%M%S")

    query = f'"{ticker}"'  # simple & robust; you can expand later
    url = "https://api.gdeltproject.org/api/v2/doc/doc"

    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "startdatetime": fmt(start),
        "enddatetime": fmt(end),
        "maxrecords": min(max_items, 250),
        "sort": "datedesc",
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    arts = data.get("articles", []) or []
    out: List[NewsItem] = []

    for a in arts:
        title = a.get("title") or ""
        link = a.get("url") or ""
        src = a.get("sourceCountry") or "gdelt"
        dt = a.get("seendate") or a.get("datetime") or a.get("date") or ""
        iso = parse_iso_datetime(dt) or datetime.now(timezone.utc).isoformat()

        out.append(NewsItem(
            published_at=iso,
            ticker=ticker.upper(),
            title=title,
            source="gdelt",
            url=link,
            summary=a.get("snippet"),
            raw={"sourceCountry": src, "domain": a.get("domain")},
        ))

    return out
