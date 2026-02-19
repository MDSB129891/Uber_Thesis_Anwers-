#!/usr/bin/env bash
set -euo pipefail

FILE="scripts/build_super_memo.py"

if [ ! -f "$FILE" ]; then
  echo "❌ Missing $FILE"
  exit 1
fi

python3 - <<'PY'
from pathlib import Path
import re

p = Path("scripts/build_super_memo.py")
txt = p.read_text(encoding="utf-8")

# 1) Insert story helper if missing
if "def build_story_layer(" not in txt:
    story = r'''
def build_story_layer(m):
    out = []
    out.append("\n## Walkthrough (like you're five)\n")

    rg = float(m.get("revenue_yoy", 0) or 0)
    fcf = float(m.get("fcf", 0) or 0)
    margin = float(m.get("fcf_margin", 0) or 0)
    debt = float(m.get("net_debt", 0) or 0)
    dy = float(m.get("fcf_yield", 0) or 0)

    out.append("### Step 1 — Are people buying more?\n")
    out.append(f"Revenue growth is {rg:.2f}%.\n")
    if rg < 0:
        out.append("Sales are shrinking. Shrinking businesses usually struggle to grow profits.\n")
    else:
        out.append("Sales are growing. Growth gives breathing room.\n")

    out.append("\n### Step 2 — Does the company actually make cash?\n")
    out.append(f"Free cash flow is ${fcf/1e9:.2f}B with margin {margin:.2f}%.\n")
    out.append("Free cash flow is money left after paying bills and necessary investments.\n")
    if margin < 10:
        out.append("Margins under 10% often mean the business works hard for little cash reward.\n")
    if fcf < 0:
        out.append("Negative free cash flow means cash is leaving the company, not entering.\n")

    out.append("\n### Step 3 — How heavy is the debt backpack?\n")
    out.append(f"Net debt is ${debt/1e9:.2f}B.\n")
    out.append("Debt is future money already spent. More debt = less flexibility.\n")

    out.append("\n### Step 4 — Is the stock cheap or expensive?\n")
    out.append(f"FCF yield is {dy:.2f}%.\n")
    out.append("FCF yield is like 'cash return' vs price. Higher can mean cheaper (if cash is real).\n")

    out.append("\n### Step 5 — Putting it together\n")
    out.append("We compare growth + cash + debt + valuation, then sanity-check with news.\n")
    out.append("If growth is weak and debt is heavy, the stock usually needs a clear turnaround story.\n")

    return "\n".join(out)
'''.lstrip("\n")

    # Put helper before main() or before "if __name__" block
    m = re.search(r"^def\s+main\(", txt, flags=re.M)
    if m:
        insert_at = m.start()
        txt = txt[:insert_at] + story + "\n\n" + txt[insert_at:]
    else:
        # fallback: add near top after imports
        m2 = re.search(r"^(import .+\n)+", txt, flags=re.M)
        insert_at = m2.end() if m2 else 0
        txt = txt[:insert_at] + "\n" + story + "\n" + txt[insert_at:]

# 2) Ensure md.append(build_story_layer(...)) is present inside main flow
if "md.append(build_story_layer(" not in txt:
    # Try common pattern: metrics = build_metrics(...) then md.append(...) sections
    # Insert right after a line that assigns metrics dict
    patterns = [
        r"^(?P<indent>\s*)metrics\s*=\s*.*\n",
        r"^(?P<indent>\s*)m\s*=\s*.*\n",
    ]
    inserted = False
    for pat in patterns:
        m = re.search(pat, txt, flags=re.M)
        if m:
            indent = m.group("indent")
            ins = f"{indent}md.append(build_story_layer(metrics))\n"
            # insert after the metrics line
            pos = m.end()
            txt = txt[:pos] + ins + txt[pos:]
            inserted = True
            break

    # If we couldn't find metrics assignment, insert after first md list creation
    if not inserted:
        m = re.search(r"^(?P<indent>\s*)md\s*=\s*\[\]\s*\n", txt, flags=re.M)
        if m:
            indent = m.group("indent")
            pos = m.end()
            txt = txt[:pos] + f"{indent}# story layer\n{indent}md.append(build_story_layer(metrics))\n" + txt[pos:]
            inserted = True

# 3) Write back
p.write_text(txt, encoding="utf-8")
print("DONE ✅ patched build_super_memo.py (story layer injected)")
PY

# compile check
python3 -m py_compile scripts/build_super_memo.py && echo "OK ✅ build_super_memo.py compiles"
