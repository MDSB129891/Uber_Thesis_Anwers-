from __future__ import annotations

# Higher = more trustworthy / less noisy
SOURCE_WEIGHTS = {
    # Tier 1 (ground truth)
    "sec": 3.0,

    # Tier 2 (high quality journalism) — keep list short & conservative
    "reuters": 2.6,
    "bloomberg": 2.6,
    "wsj": 2.3,
    "ft": 2.3,

    # Tier 3 (still useful, but noisier)
    "cnbc": 1.6,

    # Aggregators (event detection, not truth)
    "finnhub": 0.7,
    "source": 0.4
}

DEFAULT_WEIGHT = 0.6

def weight_for_source(source: str) -> float:
    if not source:
        return DEFAULT_WEIGHT
    return SOURCE_WEIGHTS.get(str(source).strip().lower(), DEFAULT_WEIGHT)
