from pathlib import Path

p = Path("scripts/build_thesis_memo.py")
txt = p.read_text(encoding="utf-8")

if "argparse.ArgumentParser" in txt:
    print("argparse already present — skipping")
    exit(0)

inject = '''
import argparse

def _get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--thesis", required=True)
    return ap.parse_args()
'''

# insert helper before main()
idx = txt.find("def main")
txt = txt[:idx] + inject + "\n\n" + txt[idx:]

# replace ticker assignment
txt = txt.replace("ticker = args.ticker.upper()", "args = _get_args()\n    ticker = args.ticker.upper()")

p.write_text(txt, encoding="utf-8")
print("DONE ✅ Restored argparse in build_thesis_memo.py")
