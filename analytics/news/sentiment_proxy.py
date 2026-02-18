from __future__ import annotations

import pandas as pd


POS_WORDS = [
    "beat", "beats", "record", "profit", "profitable", "surge", "raises", "raise guidance",
    "upgrade", "upgrades", "strong", "growth", "buyback", "expanded", "expands"
]
NEG_WORDS = [
    "investigation", "probe", "lawsuit", "sued", "strike", "ban", "regulator", "crash",
    "fatal", "recall", "decline", "miss", "misses", "downgrade", "downgrades",
    "cuts", "cut guidance", "fraud", "settlement"
]


def _count_hits(title: str, words: list) -> int:
    t = (title or "").lower()
    return sum(1 for w in words if w in t)


def build_news_sentiment_proxy(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds a simple but useful proxy score per ticker.

    proxy_score starts near 50 and moves:
      +2 per positive keyword hit
      -3 per negative article (impact_score < 0)
      + shock (sum of negative impact_score values, e.g., -7 reduces score)
      -1 per negative keyword hit
    Clamped to 0..100.

    Output is per ticker with 7d + 30d stats.
    """
    if news_df is None or news_df.empty:
        return pd.DataFrame(
            columns=[
                "ticker",
                "articles_7d", "articles_30d",
                "neg_7d", "neg_30d",
                "shock_7d", "shock_30d",
                "pos_hits_7d", "neg_hits_7d",
                "proxy_score_7d", "proxy_score_30d",
            ]
        )

    df = news_df.copy()
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["title"] = df["title"].astype(str).fillna("")
    df["impact_score"] = pd.to_numeric(df["impact_score"], errors="coerce").fillna(0).astype(int)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)

    now = pd.Timestamp.utcnow()
    df["age_days"] = (now - df["published_at"]).dt.total_seconds() / 86400.0

    df["pos_hits"] = df["title"].apply(lambda t: _count_hits(t, POS_WORDS))
    df["neg_hits"] = df["title"].apply(lambda t: _count_hits(t, NEG_WORDS))

    rows = []
    for tkr, g in df.groupby("ticker"):
        g7 = g[g["age_days"] <= 7]
        g30 = g[g["age_days"] <= 30]

        def _agg(h: pd.DataFrame, label: str):
            articles = int(len(h))
            neg = int((h["impact_score"] < 0).sum())
            shock = int(h.loc[h["impact_score"] < 0, "impact_score"].sum())  # negative
            pos_hits = int(h["pos_hits"].sum())
            neg_hits = int(h["neg_hits"].sum())

            proxy = 50 + (pos_hits * 2) - (neg * 3) + shock - (neg_hits * 1)
            proxy = max(0, min(100, int(round(proxy))))
            return articles, neg, shock, pos_hits, neg_hits, proxy

        a7, n7, s7, p7, nh7, ps7 = _agg(g7, "7d")
        a30, n30, s30, p30, nh30, ps30 = _agg(g30, "30d")

        rows.append(
            {
                "ticker": tkr,
                "articles_7d": a7,
                "articles_30d": a30,
                "neg_7d": n7,
                "neg_30d": n30,
                "shock_7d": s7,
                "shock_30d": s30,
                "pos_hits_7d": p7,
                "neg_hits_7d": nh7,
                "proxy_score_7d": ps7,
                "proxy_score_30d": ps30,
            }
        )

    out = pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)
    return out
