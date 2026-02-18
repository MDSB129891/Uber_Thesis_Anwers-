from __future__ import annotations

import pandas as pd


def build_news_risk_dashboard(news_df: pd.DataFrame, days_short: int = 7, days_long: int = 30) -> pd.DataFrame:
    """
    User-friendly dashboard of risk tags per ticker:
      - counts in last 7d and 30d (negatives only)
      - total negative impact ("shock") in last 7d and 30d
      - worst (most negative) headline in last 7d for each risk_tag
      - adds a TOTAL row per ticker
      - fills blanks with clean defaults (None/0)
    """
    cols = [
        "ticker", "risk_tag",
        "neg_count_30d", "shock_30d",
        "neg_count_7d", "shock_7d",
        "worst_7d_title", "worst_7d_source", "worst_7d_url", "worst_7d_impact",
    ]

    if news_df is None or news_df.empty:
        return pd.DataFrame(columns=cols)

    df = news_df.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["risk_tag"] = df["risk_tag"].astype(str).fillna("OTHER")
    df["impact_score"] = pd.to_numeric(df["impact_score"], errors="coerce").fillna(0).astype(float)

    now = pd.Timestamp.utcnow()
    df["age_days"] = (now - df["published_at"]).dt.total_seconds() / 86400.0

    d7 = df[df["age_days"] <= days_short].copy()
    d30 = df[df["age_days"] <= days_long].copy()

    # Negatives only
    d7n = d7[d7["impact_score"] < 0].copy()
    d30n = d30[d30["impact_score"] < 0].copy()

    # Aggregate counts + shock
    g7 = (
        d7n.groupby(["ticker", "risk_tag"])
        .agg(neg_count_7d=("impact_score", "count"), shock_7d=("impact_score", "sum"))
        .reset_index()
    )
    g30 = (
        d30n.groupby(["ticker", "risk_tag"])
        .agg(neg_count_30d=("impact_score", "count"), shock_30d=("impact_score", "sum"))
        .reset_index()
    )

    dash = g30.merge(g7, on=["ticker", "risk_tag"], how="outer")

    dash["neg_count_7d"] = pd.to_numeric(dash.get("neg_count_7d"), errors="coerce").fillna(0).astype(int)
    dash["neg_count_30d"] = pd.to_numeric(dash.get("neg_count_30d"), errors="coerce").fillna(0).astype(int)
    dash["shock_7d"] = pd.to_numeric(dash.get("shock_7d"), errors="coerce").fillna(0).astype(float)
    dash["shock_30d"] = pd.to_numeric(dash.get("shock_30d"), errors="coerce").fillna(0).astype(float)

    # Worst headline per ticker/tag in last 7d (most negative impact_score)
    worst = None
    if not d7n.empty:
        idx = d7n.groupby(["ticker", "risk_tag"])["impact_score"].idxmin()
        worst = d7n.loc[idx, ["ticker", "risk_tag", "title", "source", "url", "impact_score"]].copy()
        worst = worst.rename(
            columns={
                "title": "worst_7d_title",
                "source": "worst_7d_source",
                "url": "worst_7d_url",
                "impact_score": "worst_7d_impact",
            }
        )

    if worst is not None:
        dash = dash.merge(worst, on=["ticker", "risk_tag"], how="left")
    else:
        dash["worst_7d_title"] = None
        dash["worst_7d_source"] = None
        dash["worst_7d_url"] = None
        dash["worst_7d_impact"] = None

    # Fill blanks with clean defaults (Upgrade A)
    dash["worst_7d_title"] = dash["worst_7d_title"].fillna("None")
    dash["worst_7d_source"] = dash["worst_7d_source"].fillna("None")
    dash["worst_7d_url"] = dash["worst_7d_url"].fillna("None")
    dash["worst_7d_impact"] = pd.to_numeric(dash["worst_7d_impact"], errors="coerce").fillna(0).astype(float)

    # Add TOTAL row per ticker (Upgrade B)
    totals = (
        dash.groupby("ticker")
        .agg(
            neg_count_30d=("neg_count_30d", "sum"),
            shock_30d=("shock_30d", "sum"),
            neg_count_7d=("neg_count_7d", "sum"),
            shock_7d=("shock_7d", "sum"),
        )
        .reset_index()
    )
    totals["risk_tag"] = "TOTAL"
    totals["worst_7d_title"] = "None"
    totals["worst_7d_source"] = "None"
    totals["worst_7d_url"] = "None"
    totals["worst_7d_impact"] = 0.0

    dash = pd.concat([totals[cols], dash[cols]], ignore_index=True)

    # Sort: TOTAL first for each ticker, then most negative shocks
    dash["_rank"] = (dash["risk_tag"] != "TOTAL").astype(int)
    dash = dash.sort_values(
        ["ticker", "_rank", "shock_7d", "shock_30d", "neg_count_7d", "neg_count_30d"],
        ascending=[True, True, True, True, False, False],
    ).drop(columns=["_rank"]).reset_index(drop=True)

    # Make shocks look nice in CSV (optional: keep as float but you can round in Excel)
    return dash
