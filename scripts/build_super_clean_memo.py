import argparse, math, json
from pathlib import Path
import pandas as pd

# --- helpers ---
def is_na(x):
    return x is None or (isinstance(x, float) and (math.isnan(x) or pd.isna(x)))

def pct(x, digits=2):
    if is_na(x): return "N/A"
    return f"{float(x):.{digits}f}%"

def money(x):
    if is_na(x): return "N/A"
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e12: return f"{sign}${x/1e12:.2f}T"
    if x >= 1e9:  return f"{sign}${x/1e9:.2f}B"
    if x >= 1e6:  return f"{sign}${x/1e6:.2f}M"
    return f"{sign}${x:,.0f}"

def xmult(x, digits=2):
    if is_na(x): return "N/A"
    return f"{float(x):.{digits}f}x"

def badge(v):
    return {"GOOD":"✅ GOOD","WATCH":"🟡 WATCH","BAD":"❌ BAD","UNKNOWN":"❓ UNKNOWN"}.get(v, v)

def classify_revenue_growth(v):
    if is_na(v): return ("UNKNOWN","N/A")
    v=float(v)
    if v>10: return ("GOOD","more than +10%")
    if v>=0: return ("WATCH","0% to +10%")
    return ("BAD","below 0%")

def classify_fcf(v):
    if is_na(v): return ("UNKNOWN","N/A")
    return ("GOOD","positive") if float(v)>0 else ("BAD","negative")

def classify_fcf_margin(v):
    if is_na(v): return ("UNKNOWN","N/A")
    v=float(v)
    if v>=10: return ("GOOD","10% or higher")
    if v>=3: return ("WATCH","3% to 10%")
    return ("BAD","below 3% (or negative)")

def classify_fcf_yield(v):
    if is_na(v): return ("UNKNOWN","N/A")
    v=float(v)
    if v>5: return ("GOOD","above 5%")
    if v>=2: return ("WATCH","2% to 5%")
    return ("BAD","below 2%")

def classify_net_debt(nd):
    if is_na(nd): return ("UNKNOWN","N/A")
    nd=float(nd)
    if nd<=0: return ("GOOD","net cash (<= 0)")
    return ("WATCH","positive net debt")

def classify_nd_to_fcf(x):
    if is_na(x): return ("UNKNOWN","N/A")
    x=float(x)
    if x<3: return ("GOOD","below 3x")
    if x<=6: return ("WATCH","3x to 6x")
    return ("BAD","above 6x")

def load_comps_row(ticker: str):
    p=Path("data/processed/comps_snapshot.csv")
    df=pd.read_csv(p)
    df["ticker"]=df["ticker"].astype(str).str.upper()
    r=df[df["ticker"]==ticker.upper()]
    if r.empty:
        raise SystemExit(f"Ticker {ticker} not found in {p}. Run: ./scripts/run_thanos.sh {ticker}")
    return r.iloc[0].to_dict()

def load_json(path: str):
    P=Path(path)
    if not P.exists(): return {}
    return json.loads(P.read_text(encoding="utf-8"))

def main(ticker: str, thesis_path: str):
    T=ticker.upper()
    row=load_comps_row(T)

    # values from comps_snapshot (your pipeline already has these)
    rev_yoy=row.get("revenue_ttm_yoy_pct")
    fcf_ttm=row.get("fcf_ttm")
    fcf_margin=row.get("fcf_margin_ttm_pct")
    cash=row.get("cash"); debt=row.get("debt"); net_debt=row.get("net_debt")
    nd_to_fcf=row.get("net_debt_to_fcf_ttm")

    # fcf yield: prefer pct, else derive from decimal if present
    fcf_yield_pct=row.get("fcf_yield_pct")
    if is_na(fcf_yield_pct):
        fy=row.get("fcf_yield")
        if not is_na(fy):
            fy=float(fy)
            fcf_yield_pct = fy*100.0 if fy<=1 else fy

    # rating/veracity if present
    ds=load_json("outputs/decision_summary.json")
    vx=load_json(f"outputs/veracity_{T}.json")
    score=ds.get("score","N/A")
    rating=ds.get("rating","N/A")
    veracity=vx.get("veracity_score", vx.get("score", "N/A"))

    thesis_text=""
    try:
        thesis=json.loads(Path(thesis_path).read_text(encoding="utf-8"))
        thesis_text=thesis.get("thesis","") or thesis.get("description","") or thesis.get("headline","")
    except Exception:
        pass

    # classifications
    c1,b1=classify_revenue_growth(rev_yoy)
    c2,b2=classify_fcf(fcf_ttm)
    c3,b3=classify_fcf_margin(fcf_margin)
    c4,b4=classify_fcf_yield(fcf_yield_pct)
    c5,_ =classify_net_debt(net_debt)
    c6,b6=classify_nd_to_fcf(nd_to_fcf)

    # clean markdown (no weird bullets)
    md=[]
    md.append(f"# SUPER (Clean) Investment Memo — {T}\n")
    md.append(f"*Generated: {pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*\n")
    md.append("## 1) Your thesis (plain English)\n")
    md.append(f"**{thesis_text or 'N/A'}**\n")
    md.append("## 2) What the model concluded (plain English)\n")
    md.append(f"- Overall rating: **{rating}** (score **{score}/100**)\n")
    md.append(f"- Evidence confidence (veracity): **{veracity}** (higher = more trustworthy coverage)\n")

    md.append("## 3) Core numbers (sanity-check)\n")
    md.append(f"- Sales growth compared to last year: **{pct(rev_yoy)}**\n")
    md.append(f"- Free cash flow over the last 12 months: **{money(fcf_ttm)}**\n")
    md.append(f"- Free cash flow margin: **{pct(fcf_margin)}**\n")
    md.append(f"- Free cash flow yield (cash vs stock price): **{pct(fcf_yield_pct)}**\n")

    md.append("## 4) Balance sheet snapshot (why debt matters)\n")
    md.append(f"- Cash: **{money(cash)}**\n")
    md.append(f"- Debt: **{money(debt)}**\n")
    md.append(f"- Net debt (debt minus cash): **{money(net_debt)}**\n")
    md.append(f"- Net debt divided by free cash flow (years-to-pay): **{xmult(nd_to_fcf)}**\n")

    md.append("## 5) Good vs Bad cheat-sheet (linked to THIS ticker)\n")
    md.append("Each line shows the rule band, then **this ticker’s value today**, then the verdict.\n")
    md.append(f"### Sales growth compared to last year\n- Rule band: {b1}\n- {T} today: **{pct(rev_yoy)}** → **{badge(c1)}**\n")
    md.append(f"### Free cash flow\n- Rule band: {b2}\n- {T} today: **{money(fcf_ttm)}** → **{badge(c2)}**\n")
    md.append(f"### Free cash flow margin\n- Rule band: {b3}\n- {T} today: **{pct(fcf_margin)}** → **{badge(c3)}**\n")
    md.append(f"### Free cash flow yield (cash vs what you pay for the stock)\n- Rule band: {b4}\n- {T} today: **{pct(fcf_yield_pct)}** → **{badge(c4)}**\n")
    md.append(f"### Net debt (debt minus cash)\n- {T} today: cash **{money(cash)}**, debt **{money(debt)}**, net debt **{money(net_debt)}** → **{badge(c5)}**\n")
    md.append(f"### Net debt divided by free cash flow (years-to-pay debt)\n- Rule band: {b6}\n- {T} today: **{xmult(nd_to_fcf)}** → **{badge(classify_nd_to_fcf(nd_to_fcf)[0])}**\n")

    md.append("## 6) What to open (dopamine, but clean)\n")
    md.append(f"- Dashboard: `outputs/decision_dashboard_{T}.html`\n")
    md.append(f"- News: `outputs/news_clickpack_{T}.html`\n")
    md.append(f"- Alerts: `outputs/alerts_{T}.json`\n")
    md.append(f"- Claim evidence: `outputs/claim_evidence_{T}.html`\n")

    out_md=Path(f"outputs/{T}_SUPER_CLEAN.md")
    out_md.write_text("\n".join(md).strip()+"\n", encoding="utf-8")
    print(f"DONE ✅ wrote {out_md}")

    # Build DOCX from markdown using your existing memo builder (stable path)
    # We’ll reuse your existing build_investment_memo docx builder if it has md->docx helper.
    # Easiest: call LibreOffice directly on a temporary .txt-as-docx is messy.
    # So: just keep MD + rely on soffice conversion only if you want.
