from pathlib import Path
import re

P = Path("scripts/build_super_memo.py")
txt = P.read_text()

# 1) Remove the accidentally injected raw story lines (anything starting with "This means GM")
txt = re.sub(r"This means GM sold LESS.*?cheaper\.", "", txt, flags=re.S)

# 2) Proper red flag explanation block (safe Python triple-quoted string)
BLOCK = '''
## What these red flags actually mean (plain English)

### 1) Revenue shrinking over the last 12 months

This means GM sold LESS than it sold the year before.

When sales fall, it usually means:
- demand is weakening
- pricing power is fading
- competition is increasing

Stocks usually dislike shrinking sales because future profits become harder.

---

### 2) Free cash flow shrinking over the last 12 months

Free cash flow is what’s left after paying ALL bills and investing in the business.

Declining free cash flow means:

- less money to pay debt
- less money to invest in electric vehicles
- less money for buybacks
- less margin for mistakes

This makes investors nervous.

---

### 3) High debt compared to cash generation

GM has a LOT of debt compared to how much cash it produces each year.

Debt payments don’t stop when business slows.

If cash weakens while debt stays high, things can spiral fast.

This raises bankruptcy or refinancing risk.

---

### 4) Lots of negative labor / insurance / regulatory headlines

In the last 30 days there were many negative stories about:

- workers and unions
- insurance costs
- government regulation

These usually mean surprise expenses or forced changes.

Markets hate uncertainty, so stocks often drop quickly on this type of news.

---

### Simple rule for beginners

If sales are falling  
AND cash is falling  
AND debt is high  
AND news is negative  

Even a “cheap” stock can keep getting cheaper.
'''

# 3) Inject block after "## 7) Red flags"
txt = re.sub(
    r"(## 7\) Red flags[^\n]*\n)",
    r"\1\n" + BLOCK + "\n",
    txt,
    count=1,
    flags=re.S
)

# 4) De-jargon
REPLACEMENTS = {
    "YoY": "compared to last year",
    "TTM": "over the last 12 months",
    "FCF": "free cash flow",
}

for k,v in REPLACEMENTS.items():
    txt = txt.replace(k, v)

P.write_text(txt, encoding="utf-8")
print("✅ SUPER memo repaired + storytime reinserted safely")
