from pathlib import Path
import re

P = Path("scripts/build_ultra_memo.py")
txt = P.read_text(encoding="utf-8")

# 1) Make ULTRA load claim evidence from multiple possible keys
txt = re.sub(
    r"claims = claim_pack\.get\(\"claims\"\) or \[\]\n",
    "claims = (\n"
    "    claim_pack.get('claims')\n"
    "    or claim_pack.get('results')\n"
    "    or claim_pack.get('items')\n"
    "    or claim_pack.get('claim_results')\n"
    "    or []\n"
    ")\n",
    txt,
    count=1,
)

# 2) Force ULTRA core numbers to prefer comps_snapshot (ticker row) to avoid UBER bleed
# We replace the core-number block by a safer version.
pattern = r"# Core numbers with fallbacks.*?fcf_yield = comps\.get\(\"fcf_yield_pct\"\).*?fcf_yield = None\n\n"
if re.search(pattern, txt, flags=re.S):
    replacement = (
        "# Core numbers (SAFE): prefer comps_snapshot row for this ticker (avoids cross-ticker bleed)\n"
        "rev_yoy = comps.get('revenue_ttm_yoy_pct')\n"
        "fcf = comps.get('fcf_ttm')\n"
        "fcf_margin = comps.get('fcf_margin_ttm_pct')\n"
        "\n"
        "# FCF yield: sometimes stored as pct, sometimes as decimal\n"
        "fcf_yield = comps.get('fcf_yield_pct')\n"
        "if (fcf_yield is None) or (isinstance(fcf_yield, float) and pd.isna(fcf_yield)):\n"
        "    fy = comps.get('fcf_yield')\n"
        "    if fy is not None and not (isinstance(fy, float) and pd.isna(fy)):\n"
        "        try:\n"
        "            fcf_yield = float(fy) * 100.0\n"
        "        except Exception:\n"
        "            fcf_yield = None\n"
        "\n"
    )
    txt = re.sub(pattern, replacement, txt, flags=re.S, count=1)

P.write_text(txt, encoding="utf-8")
print("DONE ✅ Patched build_ultra_memo.py (claims + safe core numbers)")
