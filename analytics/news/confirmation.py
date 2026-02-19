from __future__ import annotations

from collections import defaultdict
from typing import Dict, Any, Set

from .source_weights import weight_for_source

def confirmed_risk_tags(
    rows: list[dict],
    min_confirmations: int = 2,
    credibility_threshold: float = 1.5
) -> Dict[str, Any]:
    """
    A tag is 'confirmed' only if it appears in >= N independent sources with weight >= credibility_threshold.
    This prevents single-source panic.
    """
    tag_sources: Dict[str, Set[str]] = defaultdict(set)

    for r in rows:
        tag = (r.get("risk_tag") or "").strip().upper()
        src = (r.get("source") or "").strip().lower()
        if not tag or tag == "OTHER":
            continue
        if weight_for_source(src) >= credibility_threshold:
            tag_sources[tag].add(src)

    confirmed = {}
    for tag, srcs in tag_sources.items():
        if len(srcs) >= min_confirmations:
            confirmed[tag] = {"confirmations": len(srcs), "sources": sorted(srcs)}

    return confirmed
