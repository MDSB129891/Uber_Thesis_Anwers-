from __future__ import annotations

from typing import List, Tuple
from .schema import NewsItem
from .utils import normalize_title


# --- Keyword dictionaries (simple, explainable, tuneable) ---
TAG_RULES: List[Tuple[str, List[str]]] = [
    ("LABOR", [
        "union", "strike", "collective bargaining", "labor", "worker", "wage", "minimum wage",
        "driver classification", "employee status", "gig worker", "contractor", "benefits",
    ]),
    ("INSURANCE", [
        "insurance", "premium", "underwriting", "claims", "liability", "coverage", "actuarial",
        "accident", "injury", "fatal", "lawsuit", "settlement",
    ]),
    ("REGULATORY", [
        "regulation", "regulatory", "ban", "permit", "license", "compliance", "antitrust",
        "probe", "investigation", "fine", "penalty", "doj", "ftc", "eu", "commission",
        "court", "appeal", "ruling",
    ]),
    ("SAFETY", [
        "safety", "assault", "harassment", "crash", "collision", "fraud", "scam",
        "data breach", "hack", "cyber", "security incident",
    ]),
    ("COMPETITION", [
        "competitor", "price war", "market share", "competition", "rival", "acquisition",
        "merger", "partnership", "exclusive",
    ]),
    ("MACRO", [
        "inflation", "recession", "rates", "interest rate", "oil", "fuel", "macro", "slowdown",
        "consumer spending", "unemployment",
    ]),
    ("FINANCIAL", [
        "earnings", "guidance", "forecast", "revenue", "profit", "loss", "margin", "cash flow",
        "buyback", "debt", "refinance", "liquidity", "bankruptcy",
    ]),
]

NEG_STRONG = [
    "lawsuit", "settlement", "strike", "ban", "investigation", "probe", "fine",
    "fatal", "killed", "fraud", "data breach", "hack", "antitrust", "penalty",
]
NEG_MED = [
    "regulation", "regulatory", "union", "injury", "accident", "complaint", "court",
    "recall", "safety", "harassment",
]
POS_MED = [
    "record", "beats", "beat", "raises guidance", "upgrade", "partnership", "expands",
    "profitable", "profit", "buyback", "cost cuts", "strong demand",
]


def tag_item(item: NewsItem) -> str:
    t = normalize_title(item.title)
    for tag, keys in TAG_RULES:
        for k in keys:
            if k in t:
                return tag
    return "OTHER"


def score_item(item: NewsItem) -> int:
    """
    Simple, explainable impact score: -3..+3 based on keywords.
    """
    t = normalize_title(item.title)

    # Strong negative signals
    for k in NEG_STRONG:
        if k in t:
            return -3

    # Medium negative
    for k in NEG_MED:
        if k in t:
            return -2

    # Medium positive
    for k in POS_MED:
        if k in t:
            return +2

    # Default neutral
    return 0


def score_and_tag(items: List[NewsItem]) -> List[NewsItem]:
    for it in items:
        it.risk_tag = tag_item(it)
        it.impact_score = score_item(it)
    return items
