from __future__ import annotations

import xml.etree.ElementTree as ET
import requests
from typing import List, Optional

from ..schema import NewsItem
from ..utils import parse_iso_datetime


def _get_text(el: Optional[ET.Element], tag: str) -> Optional[str]:
    if el is None:
        return None
    child = el.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def fetch_rss_feed(ticker: str, feed_url: str, source_name: str, max_items: int = 50) -> List[NewsItem]:
    """
    Generic RSS fetcher for company IR / press release feeds.
    """
    r = requests.get(feed_url, timeout=30)
    r.raise_for_status()

    root = ET.fromstring(r.text)
    channel = root.find("channel")
    if channel is None:
        return []

    out: List[NewsItem] = []
    for item in channel.findall("item"):
        title = _get_text(item, "title") or ""
        link = _get_text(item, "link") or ""
        pub = _get_text(item, "pubDate") or _get_text(item, "date") or ""
        iso = parse_iso_datetime(pub) or None
        if not iso:
            # still keep it
            iso = "1970-01-01T00:00:00+00:00"

        out.append(NewsItem(
            published_at=iso,
            ticker=ticker.upper(),
            title=title,
            source=source_name,
            url=link,
            summary=_get_text(item, "description"),
            raw={"feed": feed_url},
        ))

        if len(out) >= max_items:
            break

    return out
