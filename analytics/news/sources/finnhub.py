from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import requests

from ..schema import NewsItem

BASE = "https://finnhub.io/api/v1"


def _key() -> str:
    k = os.getenv("FINNHUB_API_KEY")
    if not k:
        raise RuntimeError("Missing FINNHUB_API_KEY (set it in .env)")
    return k


def _get(url: str, params: dict, timeout: int = 30, retries: int = 2) -> requests.Response:
    last_err: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(1.5 * (i + 1))
                continue
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"Finnhub request failed: {last_err}")


def fetch_finnhub_company_news(ticker: str, days_back: int = 30, max_items: int = 200) -> List[NewsItem]:
    """
    Stable per-article news endpoint (works on free keys).
    """
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days_back)

    url = f"{BASE}/company-news"
    params = {
        "symbol": ticker.upper(),
        "from": start.isoformat(),
        "to": end.isoformat(),
        "token": _key(),
    }

    r = _get(url, params=params, timeout=30, retries=2)
    data = r.json()
    if not isinstance(data, list):
        return []

    out: List[NewsItem] = []
    for a in data[:max_items]:
        ts = a.get("datetime")
        try:
            iso = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
        except Exception:
            iso = datetime.now(timezone.utc).isoformat()

        out.append(
            NewsItem(
                published_at=iso,
                ticker=ticker.upper(),
                title=a.get("headline") or "",
                source="finnhub",
                url=a.get("url") or "",
                summary=a.get("summary"),
                raw={
                    "category": a.get("category"),
                    "source": a.get("source"),
                    "related": a.get("related"),
                    "id": a.get("id"),
                    "image": a.get("image"),
                },
            )
        )
    return out
