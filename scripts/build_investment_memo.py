#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
EXPORT = ROOT / "export"
THESES = ROOT / "theses"

OUTPUTS.mkdir(parents=True, exist_ok=True)
EXPORT.mkdir(parents=True, exist_ok=True)
THESES.mkdir(parents=True, exist_ok=True)

DEFAULT_TICKER = "UBER"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def coerce_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, str) and x.strip() == "":
            return None
        return float(x)
    except Exception:
        return None


def fmt_money(x: Any) -> str:
    v = coerce_float(x)
    if v is None:
        return "N/A"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e12:
        return f"{sign}${v/1e12:.2f}T"
    if v >= 1e9:
        return f"{sign}${v/1e9:.2f}B"
    if v >= 1e6:
        return f"{sign}${v/1e6:.2f}M"
    return f"{sign}${v:,.0f}"


def fmt_pct(x: Any) -> str:
    v = coerce_float(x)
    if v is None:
        return "N/A"
    return f"{v:.1f}%"


def fmt_num(x: Any) -> str:
    v = coerce_float(x)
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:.2f}"


def risk_metric_key(tag: str, window: str) -> str:
    return f"risk_{tag.lower()}_neg_{window}"


@dataclass
class Explain:
    key: str
    title: str
    what: str
    why: str
    guide: str
    kind: str  # pct | money | num


EXPLAINS: Dict[str, Explain] = {
    "latest_revenue_yoy_pct": Explain(
        "latest_revenue_yoy_pct",
        "Revenue growth (year over year)",
        "How much sales grew compared to last year.",
        "Growing sales usually means demand is increasing and the company is scaling.",
        "Rule of thumb: <5% slow, 5–10% okay, 10%+ healthy, 20%+ very strong.",
        "pct",
    ),
    "latest_free_cash_flow": Explain(
        "latest_free_cash_flow",
        "Free Cash Flow (FCF)",
        "Real cash left after paying operating costs AND necessary investments (capex).",
        "Positive FCF means the company funds itself (less need for debt or dilution).",
        "Rule of thumb: negative for long periods is risky; positive and rising is strong.",
        "money",
    ),
    "latest_fcf_margin_pct": Explain(
        "latest_fcf_margin_pct",
        "FCF margin",
        "How much of revenue turns into free cash (as a percent).",
        "Shows efficiency: high margin means sales turn into real money.",
        "Rule of thumb: <5% weak, 5–10% okay, 10–15% good, 15%+ excellent.",
        "pct",
    ),
    "fcf_yield_pct": Explain(
        "fcf_yield_pct",
        "FCF yield (valuation vs cash)",
        "Free cash flow divided by market value. Think: 'cash return' if cash stayed stable.",
        "Higher yield usually means the stock is cheaper relative to its cash generation.",
        "Rule of thumb: <2% expensive, 2–4% fair, 4–6% attractive, 6%+ cheap.",
        "pct",
    ),
    "news_shock_30d": Explain(
        "news_shock_30d",
        "News shock (last 30 days)",
        "A warning-light score that gets worse when negative news spikes recently.",
        "Helps detect if risks are getting louder (lawsuits, regulation, safety, insurance issues).",
        "Closer to 0 is better; more negative is worse. Use as a signal, not absolute truth.",
        "num",
    ),
    "latest_cash": Explain(
        "latest_cash",
        "Cash on hand",
        "How much cash the company has available.",
        "More cash can help survive shocks and invest without borrowing.",
        "Rule of thumb: more is safer, but what matters is cash relative to debt and cash generation.",
        "money",
    ),
    "latest_debt": Explain(
        "latest_debt",
        "Total debt",
        "Money the company owes to lenders.",
        "Debt increases risk if the business hits trouble or interest rates rise.",
        "Rule of thumb: debt is okay if the company generates enough cash to manage it.",
        "money",
    ),
    "latest_net_debt": Explain(
        "latest_net_debt",
        "Net debt",
        "Debt minus cash. If negative, the company has more cash than debt.",
        "Net debt is a cleaner picture of financial risk than debt alone.",
        "Lower is safer. Negative net debt is usually very safe.",
        "money",
    ),
    "latest_net_debt_to_fcf": Explain(
        "latest_net_debt_to_fcf",
        "Net debt to FCF (years to pay off debt with cash)",
        "Roughly: how many years of current free cash flow would pay off net debt.",
        "This is an intuitive risk gauge: fewer years = easier to handle debt.",
        "Rule of thumb: <2 low risk, 2–4 okay, 4+ watch carefully (depends on stability).",
        "num",
    ),
}


def explain_risk_tag(key: str) -> Optional[Explain]:
    if not (key.startswith("risk_") and key.endswith("_neg_30d")):
        return None
    tag = key.replace("risk_", "").replace("_neg_30d", "").upper()
    return Explain(
        key=key,
        title=f"{tag.title()} risk (negative items in last 30 days)",
        what=f"How many recent negative items were tagged as {tag}.",
        why="Repeated negatives in the same theme can be a real risk, not just random noise.",
        guide="Rule of thumb: 0–3 is usually manageable; repeated spikes deserve deep reading.",
        kind="num",
    )


def format_value(metric_key: str, value: Any) -> str:
    ex = EXPLAINS.get(metric_key) or explain_risk_tag(metric_key)
    if ex is None:
        v = coerce_float(value)
        return str(value) if v is None else fmt_num(v)

    if ex.kind == "pct":
        return fmt_pct(value)
    if ex.kind == "money":
        return fmt_money(value)
    return fmt_num(value)


def build_metrics_snapshot(ticker: str) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}

    f = safe_read_csv(DATA_PROCESSED / "fundamentals_annual_history.csv")
    if not f.empty:
        if "period_end" in f.columns:
            f = f.sort_values("period_end")
        last = f.iloc[-1]
        metrics["latest_period_end"] = last.get("period_end")
        metrics["latest_revenue_yoy_pct"] = last.get("revenue_yoy_pct")
        metrics["latest_free_cash_flow"] = last.get("free_cash_flow")
        metrics["latest_fcf_margin_pct"] = last.get("fcf_margin_pct")

        cash = coerce_float(last.get("cash"))
        debt = coerce_float(last.get("debt"))
        metrics["latest_cash"] = cash
        metrics["latest_debt"] = debt
        if cash is not None and debt is not None:
            metrics["latest_net_debt"] = debt - cash
            fcf = coerce_float(metrics.get("latest_free_cash_flow"))
            if fcf and fcf != 0:
                metrics["latest_net_debt_to_fcf"] = (debt - cash) / fcf

    comps = safe_read_csv(DATA_PROCESSED / "comps_snapshot.csv")
    if not comps.empty and "ticker" in comps.columns:
        r = comps[comps["ticker"].astype(str).str.upper() == ticker.upper()]
        if not r.empty:
            row = r.iloc[0].to_dict()
            metrics["price"] = row.get("price")
            metrics["market_cap"] = row.get("market_cap")
            fy = row.get("fcf_yield")
            if fy is not None:
                try:
                    metrics["fcf_yield_pct"] = float(fy) * 100.0
                except Exception:
                    metrics["fcf_yield_pct"] = fy

    proxy = safe_read_csv(DATA_PROCESSED / "news_sentiment_proxy.csv")
    if not proxy.empty and "ticker" in proxy.columns:
        r = proxy[proxy["ticker"].astype(str).str.upper() == ticker.upper()]
        if not r.empty:
            row = r.iloc[0].to_dict()
            metrics["news_shock_30d"] = row.get("shock_30d")
            metrics["news_neg_30d"] = row.get("neg_30d")
            metrics["news_articles_30d"] = row.get("articles_30d")
            metrics["news_proxy_score_30d"] = row.get("proxy_score_30d")

    risk = safe_read_csv(DATA_PROCESSED / "news_risk_dashboard.csv")
    if not risk.empty and "ticker" in risk.columns:
        rd = risk[risk["ticker"].astype(str).str.upper() == ticker.upper()].copy()
        if not rd.empty and "risk_tag" in rd.columns:
            alias = {"LABOUR": "LABOR", "WORKFORCE": "LABOR", "EMPLOYMENT": "LABOR"}
            for _, rr in rd.iterrows():
                raw_tag = str(rr.get("risk_tag", "OTHER")).strip().upper()
                tag = alias.get(raw_tag, raw_tag)
                metrics[risk_metric_key(tag, "30d")] = rr.get("neg_count_30d")

    for t in ["insurance", "regulatory", "labor", "safety"]:
        metrics.setdefault(f"risk_{t}_neg_30d", 0)

    return metrics


def op_ok(value: Optional[float], op: str, threshold: float) -> Optional[bool]:
    if value is None:
        return None
    if op == ">=":
        return value >= threshold
    if op == ">":
        return value > threshold
    if op == "<=":
        return value <= threshold
    if op == "<":
        return value < threshold
    if op in ("==", "="):
        return value == threshold
    return None


def eval_thesis(thesis: dict, metrics: Dict[str, Any]) -> Tuple[float, int, int, List[dict]]:
    earned = 0
    total = 0
    results: List[dict] = []

    for c in thesis.get("claims", []) or []:
        weight = int(coerce_float(c.get("weight")) or 1)
        total += weight

        mkey = c.get("metric")
        raw = metrics.get(mkey)
        val = coerce_float(raw)

        thr = coerce_float(c.get("threshold"))
        ok = None if thr is None else op_ok(val, str(c.get("operator", "")).strip(), float(thr))

        if ok is True:
            status = "PASS"
            earned += weight
        elif ok is False:
            status = "FAIL"
        else:
            status = "UNKNOWN"

        results.append({
            "id": c.get("id", mkey),
            "statement": c.get("statement", ""),
            "metric": mkey,
            "operator": c.get("operator"),
            "threshold": thr,
            "weight": weight,
            "value": raw,
            "status": status,
        })

    support_pct = round(100.0 * earned / max(1, total), 1)
    return support_pct, earned, total, results


def thesis_files_for(ticker: str) -> Dict[str, Path]:
    base = THESES / f"{ticker}_thesis_base.json"
    bull = THESES / f"{ticker}_thesis_bull.json"
    bear = THESES / f"{ticker}_thesis_bear.json"
    legacy = THESES / f"{ticker}_thesis.json"

    files: Dict[str, Path] = {}
    if base.exists():
        files["base"] = base
    elif legacy.exists():
        files["base"] = legacy
    if bull.exists():
        files["bull"] = bull
    if bear.exists():
        files["bear"] = bear
    return files


def weighted_support(supports: Dict[str, float], weights: Dict[str, float]) -> float:
    num = 0.0
    den = 0.0
    for k, s in supports.items():
        w = weights.get(k, 0.0)
        num += w * s
        den += w
    return round((num / den), 1) if den > 0 else supports.get("base", 0.0)


def scenario_explainer(name: str) -> str:
    if name == "bear":
        return ("Bear case: things go wrong (growth slows, costs rise, risks escalate). "
                "If the thesis holds here, it’s more resilient.")
    if name == "bull":
        return ("Bull case: things go right (strong execution + contained risks). "
                "If the thesis holds here, there may be meaningful upside.")
    return ("Base case: the most likely world (the company continues roughly as it is today). "
            "This is the main thesis you’re betting on.")


def build_plain_english_section(metrics: Dict[str, Any], used_keys: List[str]) -> str:
    seen = set()
    keys: List[str] = []
    for k in used_keys:
        if k and k not in seen:
            keys.append(k)
            seen.add(k)

    for k in sorted(metrics.keys()):
        if k.startswith("risk_") and k.endswith("_neg_30d") and k not in seen:
            keys.append(k)
            seen.add(k)

    lines: List[str] = []
    lines.append("## Plain-English explanations (for beginners)")
    lines.append("")
    for k in keys:
        ex = EXPLAINS.get(k) or explain_risk_tag(k)
        if not ex:
            continue
        lines.append(f"### {ex.title}")
        lines.append(f"**Actual:** {format_value(k, metrics.get(k))}")
        lines.append(f"**What it is:** {ex.what}")
        lines.append(f"**Why it matters:** {ex.why}")
        lines.append(f"**How to judge it:** {ex.guide}")
        lines.append("")
    return "\n".join(lines)


def build_next_steps() -> str:
    return "\n".join([
        "## Next steps (idiot-proof checklist)",
        "",
        "1) Read the Base case. If Base support is high, the thesis is supported today.",
        "2) Check the Bear case. If Bear support is decent, the thesis survives stress.",
        "3) Check the Bull case. If Bull support is high too, there may be upside.",
        "4) If confidence is low (single-source news), click-verify the worst headlines first.",
        "5) Re-run weekly or monthly to monitor changes.",
        "",
    ])


def doc_add_title(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)


def doc_add_small(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    for r in p.runs:
        r.font.size = Pt(10)


def doc_add_h1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)


def doc_add_h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)


def doc_add_lines(doc: Document, text: str) -> None:
    for line in text.split("\n"):
        doc.add_paragraph(line)


def main():
    ticker = DEFAULT_TICKER

    # decision summary
    decision = safe_read_json(OUTPUTS / "decision_summary.json")
    rating = decision.get("rating")
    score = decision.get("score")

    # veracity (created by build_veracity_pack.py)
    veracity = safe_read_json(OUTPUTS / f"veracity_{ticker}.json")
    confidence = veracity.get("confidence_score")
    must_click = veracity.get("must_click") or []

    metrics = build_metrics_snapshot(ticker)
    files = thesis_files_for(ticker)
    if "base" not in files:
        raise FileNotFoundError(f"Missing base thesis file. Run: python3 scripts/generate_thesis_suite.py")

    suite: Dict[str, dict] = {}
    supports: Dict[str, float] = {}

    for name, path in files.items():
        thesis = safe_read_json(path)
        support, earned, total, results = eval_thesis(thesis, metrics)
        suite[name] = {"thesis": thesis, "support_pct": support, "results": results}
        supports[name] = support

    weights = {"bear": 0.25, "base": 0.50, "bull": 0.25}
    weighted = weighted_support(supports, weights)

    used_keys = [r["metric"] for r in suite["base"]["results"] if r.get("metric")]

    md: List[str] = []
    md.append(f"# Full Investment Memo — {ticker}")
    md.append(f"*Generated: {utc_now()}*")
    md.append("")
    md.append("## Quick summary (for busy humans)")
    if rating is not None and score is not None:
        md.append(f"- Model rating: **{rating}** (score {score}/100)")
    md.append(f"- Thesis support (Base): **{suite['base']['support_pct']}%**")
    if "bear" in suite:
        md.append(f"- Thesis support (Bear): **{suite['bear']['support_pct']}%**")
    if "bull" in suite:
        md.append(f"- Thesis support (Bull): **{suite['bull']['support_pct']}%**")
    md.append(f"- Probability-weighted support: **{weighted}%** (weights {weights})")
    md.append(f"- Confidence / veracity: **{confidence}/100**" if confidence is not None else "- Confidence / veracity: **N/A** (run build_veracity_pack)")
    md.append("")

    md.append("## Evidence to verify (Top 10 must-click headlines)")
    if must_click:
        md.append("Click these first. If the same theme repeats, treat it as more serious.")
        for it in must_click[:10]:
            title = it.get("title", "(no title)")
            url = it.get("url", "")
            src = it.get("source", "")
            tag = it.get("risk_tag", "")
            imp = it.get("impact_score", "")
            if url:
                md.append(f"- [{title}]({url}) — {src} | {tag} | impact {imp}")
            else:
                md.append(f"- {title} — {src} | {tag} | impact {imp}")
    else:
        md.append("- Not available yet. Run: `python3 scripts/build_veracity_pack.py`")
    md.append("")

    md.append("## The thesis (Base case)")
    md.append(f"**{suite['base']['thesis'].get('name','')}**")
    md.append(suite["base"]["thesis"].get("description",""))
    md.append("")

    md.append("## Scenarios (Bear / Base / Bull)")
    for scenario in ["bear", "base", "bull"]:
        if scenario not in suite:
            continue
        s = suite[scenario]
        md.append(f"### {scenario.upper()} — support {s['support_pct']}%")
        md.append(scenario_explainer(scenario))
        md.append("")
        md.append("Claims checklist:")
        for r in s["results"]:
            actual = format_value(r["metric"], r["value"])
            md.append(f"- **{r['status']}** — {r['statement']}  \n  Metric `{r['metric']}` | Actual: **{actual}**")
        md.append("")

    md.append(build_plain_english_section(metrics, used_keys))
    md.append(build_next_steps())

    md_path = OUTPUTS / f"{ticker}_Full_Investment_Memo.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    doc = Document()
    doc_add_title(doc, f"Full Investment Memo — {ticker}")
    doc_add_small(doc, f"Generated: {utc_now()}")

    doc_add_h1(doc, "Quick summary")
    if rating is not None and score is not None:
        doc_add_lines(doc, f"Model rating: {rating} (score {score}/100)")
    doc_add_lines(doc, f"Base support: {suite['base']['support_pct']}%")
    if "bear" in suite:
        doc_add_lines(doc, f"Bear support: {suite['bear']['support_pct']}%")
    if "bull" in suite:
        doc_add_lines(doc, f"Bull support: {suite['bull']['support_pct']}%")
    doc_add_lines(doc, f"Probability-weighted support: {weighted}% (weights {weights})")
    doc_add_lines(doc, f"Confidence / veracity: {confidence}/100" if confidence is not None else "Confidence / veracity: N/A")

    doc_add_h1(doc, "Evidence to verify (Top 10 must-click headlines)")
    if must_click:
        for it in must_click[:10]:
            doc_add_lines(doc, f"- {it.get('title','(no title)')} | {it.get('source','')} | {it.get('risk_tag','')} | impact {it.get('impact_score','')} | {it.get('url','')}")
    else:
        doc_add_lines(doc, "Not available yet. Run: python3 scripts/build_veracity_pack.py")

    doc_add_h1(doc, "The thesis (Base case)")
    doc_add_h2(doc, suite["base"]["thesis"].get("name",""))
    doc_add_lines(doc, suite["base"]["thesis"].get("description",""))

    doc_add_h1(doc, "Scenarios (Bear / Base / Bull)")
    for scenario in ["bear", "base", "bull"]:
        if scenario not in suite:
            continue
        s = suite[scenario]
        doc_add_h2(doc, f"{scenario.upper()} — support {s['support_pct']}%")
        doc_add_lines(doc, scenario_explainer(scenario))
        doc_add_lines(doc, "Claims checklist:")
        for r in s["results"]:
            actual = format_value(r["metric"], r["value"])
            doc_add_lines(doc, f"- {r['status']} — {r['statement']} | {r['metric']} | Actual: {actual}")

    doc_add_h1(doc, "Plain-English explanations")
    doc_add_lines(doc, build_plain_english_section(metrics, used_keys))

    doc_add_h1(doc, "Next steps")
    doc_add_lines(doc, build_next_steps())

    docx_path = EXPORT / f"{ticker}_Full_Investment_Memo.docx"
    doc.save(docx_path)

    print("DONE ✅ Memo created:")
    print(f"- {md_path}")
    print(f"- {docx_path}")


if __name__ == "__main__":
    main()
