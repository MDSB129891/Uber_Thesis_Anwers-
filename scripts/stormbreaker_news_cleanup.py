#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

def domain_of(url: str) -> str:
    try:
        return (urlparse(str(url)).netloc or "").lower()
    except Exception:
        return ""

def load_whitelist_domains() -> set[str]:
    wl = ROOT / "export" / "source_whitelist.csv"
    if not wl.exists():
        return set()
    try:
        df = pd.read_csv(wl)
        # accept either "domain" column or single-column csv
        if "domain" in df.columns:
            return set(df["domain"].dropna().astype(str).str.lower().str.strip())
        return set(df.iloc[:,0].dropna().astype(str).str.lower().str.strip())
    except Exception:
        return set()

def source_weight(source: str) -> float:
    # Keep conservative (you can tune later)
    s = (source or "").strip().lower()
    if s == "sec":
        return 3.0
    if s in {"reuters","bloomberg","wsj","ft"}:
        return 2.5
    if s in {"cnbc"}:
        return 1.6
    if s in {"finnhub"}:
        return 0.7
    return 0.6

def main(ticker: str):
    in_path = PROCESSED / "news_unified.csv"
    if not in_path.exists():
        print("No news_unified.csv found. Skipping.")
        return

    df = pd.read_csv(in_path)
    if df.empty:
        print("news_unified.csv empty. Skipping.")
        return

    # Basic normalization
    df["ticker"] = df.get("ticker", "").astype(str).str.upper()
    df = df[df["ticker"] == ticker.upper()].copy()

    if df.empty:
        print(f"No rows for {ticker} in news_unified.csv. Skipping.")
        return

    df["domain"] = df.get("url", "").apply(domain_of)
    df["src_weight"] = df.get("source", "").apply(source_weight)

    whitelist = load_whitelist_domains()
    df["whitelisted"] = df["domain"].isin(whitelist)

    # Boost whitelisted domains a bit
    df["trust_score"] = df["src_weight"] + df["whitelisted"].astype(int) * 0.5

    # Dedupe strategy:
    # 1) Prefer existing dedupe_key if present
    # 2) Otherwise dedupe on (published day, normalized title)
    if "dedupe_key" in df.columns:
        df = df.sort_values(["trust_score"], ascending=False).drop_duplicates(subset=["dedupe_key"], keep="first")
    else:
        df["published_day"] = df.get("published_at", "").astype(str).str.slice(0, 10)
        df["title_norm"] = df.get("title", "").astype(str).str.lower().str.replace(r"\W+", " ", regex=True).str.strip()
        df = df.sort_values(["trust_score"], ascending=False).drop_duplicates(subset=["published_day","title_norm"], keep="first")

    # Keep most useful columns and sort newest first
    cols = [c for c in [
        "published_at","ticker","title","source","domain","url","summary","risk_tag","impact_score","sentiment","whitelisted","trust_score","dedupe_key"
    ] if c in df.columns]
    df = df[cols].copy()
    df = df.sort_values("published_at", ascending=False)

    out_path = PROCESSED / "news_unified_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"DONE ✅ news cleanup: {out_path} (rows={len(df)})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    args = ap.parse_args()
    main(args.ticker)
