from pathlib import Path
import re

P = Path("scripts/build_super_memo.py")
txt = P.read_text(encoding="utf-8")

# 0) Sanity: if file is already broken, stop before making it worse
if "SyntaxError" in txt:
    raise SystemExit("build_super_memo.py contains 'SyntaxError' text inside it. Open it and remove that first.")

# 1) Ensure we have ONE safe de-jargon helper
if "_de_jargon(" not in txt:
    helper = r'''
def _de_jargon(s: str) -> str:
    if not isinstance(s, str):
        return s
    # Replace common finance abbreviations with plain English
    repl = [
        (r"\bYoY\b", "compared to last year"),
        (r"\bTTM\b", "over the last 12 months"),
        (r"\bLTM\b", "over the last 12 months"),
        (r"\bFCF\b", "free cash flow"),
        (r"\bEPS\b", "earnings per share"),
        (r"\bEV\b", "enterprise value"),
        (r"\bEBITDA\b", "earnings before interest, taxes, depreciation, and amortization"),
    ]
    out = s
    for pat, rep in repl:
        out = re.sub(pat, rep, out)
    return out
'''
    # Inject after imports
    m = re.search(r"^\s*import\s+.+$", txt, flags=re.M)
    if not m:
        txt = "import re\n" + txt
        insert_at = 0
    else:
        # after last import block
        imports = list(re.finditer(r"^\s*(import|from)\s+.+$", txt, flags=re.M))
        insert_at = imports[-1].end()
    txt = txt[:insert_at] + "\n" + helper + "\n" + txt[insert_at:]

# Make sure 're' is imported (needed for _de_jargon)
if "import re" not in txt:
    txt = "import re\n" + txt

# 2) Add the Good/Bad + Storytime builders (safe Python code, no naked text)
if "def _build_good_bad_block(" not in txt:
    builders = r'''
def _fmt_pct(x):
    try:
        if x is None:
            return "N/A"
        return f"{float(x):.2f}%"
    except Exception:
        return "N/A"

def _fmt_money(x):
    try:
        if x is None:
            return "N/A"
        v = float(x)
        sign = "-" if v < 0 else ""
        v = abs(v)
        if v >= 1e12: return f"{sign}${v/1e12:.2f}T"
        if v >= 1e9:  return f"{sign}${v/1e9:.2f}B"
        if v >= 1e6:  return f"{sign}${v/1e6:.2f}M"
        return f"{sign}${v:,.0f}"
    except Exception:
        return "N/A"

def _status_from_band(value, good_min=None, ok_min=None, bad_max=None):
    # Returns ("GOOD"/"OK"/"BAD"/"UNKNOWN", emoji)
    try:
        if value is None:
            return ("UNKNOWN", "❓")
        v = float(value)
    except Exception:
        return ("UNKNOWN", "❓")

    # If using min bands
    if good_min is not None and ok_min is not None:
        if v >= good_min: return ("GOOD", "✅")
        if v >= ok_min:   return ("OK", "🟡")
        return ("BAD", "❌")

    # If using max band (e.g., leverage)
    if bad_max is not None and ok_min is not None:
        if v <= ok_min:   return ("GOOD", "✅")
        if v <= bad_max:  return ("OK", "🟡")
        return ("BAD", "❌")

    return ("UNKNOWN", "❓")

def _pick(metrics: dict, *keys):
    for k in keys:
        if k in metrics and metrics[k] is not None:
            return metrics[k]
    return None

def _build_good_bad_block(metrics: dict) -> str:
    # pull metrics (best-effort across your pipeline naming)
    rev_g = _pick(metrics, "revenue_ttm_yoy_pct", "latest_revenue_yoy_pct")
    fcf   = _pick(metrics, "fcf_ttm", "latest_free_cash_flow", "free_cash_flow")
    fcf_m = _pick(metrics, "fcf_margin_ttm_pct", "latest_fcf_margin_pct")
    fcf_y = _pick(metrics, "fcf_yield_pct", "fcf_yield")  # could be percent or decimal depending on source
    netd  = _pick(metrics, "net_debt")
    nd_f  = _pick(metrics, "net_debt_to_fcf_ttm", "net_debt_to_fcf")
    shock = _pick(metrics, "news_shock_30d")

    # normalize yield if it's decimal (0.08) vs percent (8)
    try:
        if fcf_y is not None:
            fy = float(fcf_y)
            if 0 < fy < 1.0:
                fcf_y = fy * 100.0
    except Exception:
        pass

    # statuses
    s_rev, e_rev = _status_from_band(rev_g, good_min=10.0, ok_min=0.0)
    s_fcm, e_fcm = _status_from_band(fcf_m, good_min=10.0, ok_min=3.0)
    s_fcy, e_fcy = _status_from_band(fcf_y, good_min=5.0, ok_min=2.0)
    s_ndf, e_ndf = _status_from_band(nd_f, ok_min=3.0, bad_max=6.0)  # <=3 good, <=6 ok, >6 bad

    # news shock: less negative is better; treat >= -15 as OK, < -15 bad
    try:
        if shock is None:
            s_sh, e_sh = ("UNKNOWN", "❓")
        else:
            sh = float(shock)
            if sh >= -10: s_sh, e_sh = ("GOOD", "✅")
            elif sh >= -15: s_sh, e_sh = ("OK", "🟡")
            else: s_sh, e_sh = ("BAD", "❌")
    except Exception:
        s_sh, e_sh = ("UNKNOWN", "❓")

    lines = []
    lines.append("## Good vs Bad cheat-sheet (how to judge the numbers)")
    lines.append("Think of every metric like a **warning light** on a car.")
    lines.append("")
    lines.append("### Revenue growth compared to last year")
    lines.append("- ✅ Usually good: **more than +10%**")
    lines.append("- 🟡 Depends: **0% to +10%**")
    lines.append("- ❌ Usually bad: **below 0%** (shrinking sales)")
    lines.append(f"- **{metrics.get('ticker','This company')} today:** **{_fmt_pct(rev_g)}** → **{s_rev}** {e_rev}")
    lines.append("")
    lines.append("### Free cash flow (cash left after bills + investment)")
    lines.append("- ✅ Good: **positive** and steady/rising")
    lines.append("- 🟡 Mixed: small positive but bouncy")
    lines.append("- ❌ Bad: negative often (burning cash)")
    lines.append(f"- **Today:** **{_fmt_money(fcf)}**")
    lines.append("")
    lines.append("### Free cash flow margin (cash per $100 of sales)")
    lines.append("- ✅ Good: **10% or higher** (industry dependent)")
    lines.append("- 🟡 Mixed: **3% to 10%**")
    lines.append("- ❌ Bad: **0% or negative**")
    lines.append(f"- **Today:** **{_fmt_pct(fcf_m)}** → **{s_fcm}** {e_fcm}")
    lines.append("")
    lines.append("### Free cash flow yield (cash return vs stock price)")
    lines.append("- ✅ Often cheap: **above 5%**")
    lines.append("- 🟡 Neutral: **2% to 5%**")
    lines.append("- ❌ Often expensive: **below 2%**")
    lines.append(f"- **Today:** **{_fmt_pct(fcf_y)}** → **{s_fcy}** {e_fcy}")
    lines.append("")
    lines.append("### Net debt divided by free cash flow (years-to-pay debt)")
    lines.append("- ✅ Good: **below 3x**")
    lines.append("- 🟡 Watch: **3x to 6x**")
    lines.append("- ❌ High risk: **above 6x**")
    lines.append(f"- **Today:** **{nd_f if nd_f is not None else 'N/A'}** → **{s_ndf}** {e_ndf}")
    lines.append("")
    lines.append("### Recent headline shock (last 30 days)")
    lines.append("- ✅ Good: mild/normal (no crisis)")
    lines.append("- 🟡 Watch: elevated negativity (verify details)")
    lines.append("- ❌ Bad: severe negative burst (can hit stock fast)")
    lines.append(f"- **Today:** **{shock if shock is not None else 'N/A'}** → **{s_sh}** {e_sh}")
    lines.append("")
    return _de_jargon("\n".join(lines))

def _build_storytime_block(ticker: str) -> str:
    t = ticker.upper()
    return _de_jargon(f"""## Storytime walkthrough (explain it like I'm five)

Okay. Imagine **{t}** is a **gigantic toy factory**.

You're asking:
**Will this factory make more money later, or get hit with expensive problems?**

### Step 1 — Sales
Sales growth means: **are more people buying the toys than last year?**

### Step 2 — Real cash (money left after everything)
**Free cash flow** is what’s left after paying **all bills** and investing in the business.
Positive = piggy bank fills. Negative = piggy bank leaks.

### Step 3 — Efficiency
**Free cash flow margin** is: out of every $100 of sales, how many dollars become real cash?

### Step 4 — Price vs cash
**Free cash flow yield** is: if you buy the stock today, how much cash do you get back relative to the price?

### Step 5 — Debt stress
**Net debt divided by free cash flow** is: how many years of today’s cash does it take to pay off debt?
If this is high, the business has less room for mistakes.

### Step 6 — Headlines
News shock is: did headlines suddenly get scary lately?
That can move the stock fast even when the business is okay.

Then the engine combines all of that into buckets (cash strength, valuation, growth, quality, and balance-sheet risk) and checks whether the facts match your thesis.
""")
'''
    # Inject builders before main()
    m = re.search(r"^def\s+main\(", txt, flags=re.M)
    if not m:
        raise SystemExit("Could not find def main(...). File structure differs.")
    txt = txt[:m.start()] + builders + "\n" + txt[m.start():]

# 3) Ensure the memo actually appends these blocks before it writes
# We will insert just before the first md_path.write_text(...) or before md_text is finalized.
insert_snippet = r'''
    # --- Inject beginner layers (Good/Bad + Storytime) ---
    try:
        md.append(_build_good_bad_block(metrics))
        md.append(_build_storytime_block(ticker))
    except Exception:
        # Don't break the memo if something is missing
        pass

    # Normalize bullets so Word/PDF doesn't scatter weird glyphs
    md = [s.replace("", "- ").replace("•", "- ") for s in md]
'''

if "Inject beginner layers" not in txt:
    # Find where md is written
    m = re.search(r"md_path\.write_text\(", txt)
    if not m:
        raise SystemExit("Could not find md_path.write_text(...). File structure differs.")
    # Insert snippet a bit before write: find prior line break and insert at indentation level
    before = txt[:m.start()]
    # Find the start of the line that contains md_path.write_text
    line_start = before.rfind("\n")
    indent = re.match(r"\s*", txt[line_start+1:m.start()]).group(0)
    # Make snippet match indent
    snippet = "\n".join(indent + ln if ln.strip() else "" for ln in insert_snippet.splitlines()) + "\n"
    txt = txt[:m.start()] + snippet + txt[m.start():]

# 4) Make sure the markdown write uses de-jargon on the final text (if it writes md_text, still ok)
# (only do if it isn't already)
if "md_path.write_text(_de_jargon" not in txt:
    txt = re.sub(
        r"md_path\.write_text\((.+?),\s*encoding=['\"]utf-8['\"]\)",
        r"md_path.write_text(_de_jargon(\1), encoding='utf-8')",
        txt,
        count=1,
        flags=re.S
    )

P.write_text(txt, encoding="utf-8")
print("DONE ✅ Patched build_super_memo.py: added Good/Bad + Storytime + de-jargon + bullet cleanup")
