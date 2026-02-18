from __future__ import annotations

from pathlib import Path
import pandas as pd


def build_evidence_table(news_df: pd.DataFrame, ticker: str, days: int = 30, max_rows: int = 80) -> pd.DataFrame:
    """
    Evidence pack you can verify:
      - filters to one ticker
      - last N days
      - sorts by worst impact first, then most recent
      - keeps URLs so you can click through
    """
    if news_df is None or news_df.empty:
        return pd.DataFrame(columns=["published_at", "ticker", "source", "risk_tag", "impact_score", "title", "url"])

    df = news_df.copy()
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df = df[df["ticker"] == ticker.upper()].copy()

    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
    df = df[df["published_at"] >= cutoff].copy()

    df["impact_score"] = pd.to_numeric(df["impact_score"], errors="coerce").fillna(0).astype(int)
    df["risk_tag"] = df["risk_tag"].astype(str).fillna("OTHER")
    df["source"] = df["source"].astype(str).fillna("unknown")
    df["title"] = df["title"].astype(str).fillna("")
    df["url"] = df["url"].astype(str).fillna("")

    # Put worst first, then newest
    df = df.sort_values(["impact_score", "published_at"], ascending=[True, False])

    keep = df[["published_at", "ticker", "source", "risk_tag", "impact_score", "title", "url"]].head(max_rows).copy()
    keep["published_at"] = keep["published_at"].dt.strftime("%Y-%m-%d %H:%M UTC")
    return keep


def write_evidence_html(evidence_df: pd.DataFrame, out_path: Path, title: str):
    """
    Writes a lightweight clickable HTML you can open in your browser.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if evidence_df is None or evidence_df.empty:
        out_path.write_text(f"<html><body><h2>{title}</h2><p>No evidence rows.</p></body></html>", encoding="utf-8")
        return

    # Make title clickable
    def linkify(row):
        u = row.get("url", "")
        t = row.get("title", "")
        if u and u != "None":
            return f'<a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'
        return t

    df = evidence_df.copy()
    df["title"] = df.apply(linkify, axis=1)

    html_table = df.to_html(index=False, escape=False)

    html = f"""
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>{title}</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; padding: 24px; }}
          h2 {{ margin: 0 0 12px 0; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 13px; vertical-align: top; }}
          th {{ background: #f5f5f5; }}
          tr:nth-child(even) {{ background: #fafafa; }}
        </style>
      </head>
      <body>
        <h2>{title}</h2>
        <p>Click any headline to open the source. Sorted by worst impact first, then newest.</p>
        {html_table}
      </body>
    </html>
    """
    out_path.write_text(html, encoding="utf-8")
