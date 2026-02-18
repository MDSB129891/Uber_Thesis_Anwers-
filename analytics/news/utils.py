from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional


_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def normalize_title(title: str) -> str:
    t = (title or "").strip().lower()
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def date_bucket(iso_dt: str) -> str:
    try:
        return str(iso_dt)[:10]
    except Exception:
        return ""


def make_dedupe_key(ticker: str, iso_dt: str, title: str) -> str:
    base = f"{(ticker or '').upper()}|{date_bucket(iso_dt)}|{normalize_title(title)}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def parse_iso_datetime(s: str) -> Optional[str]:
    """
    Best-effort parse various datetime formats into ISO (UTC if naive).
    Returns ISO string or None.
    """
    if not s:
        return None
    s = str(s).strip()

    # Already ISO-ish
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    # RFC2822-ish (RSS)
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None
