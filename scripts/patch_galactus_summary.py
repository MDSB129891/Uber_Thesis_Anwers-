from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/run_uber_update.py")

HELPER = r'''
def write_ticker_json(outputs_dir, ticker: str, basename: str, obj: dict) -> str:
    """
    Writes BOTH:
      1) outputs/<basename>_<TICKER>.json  (ticker-scoped, never overwritten by other tickers)
      2) outputs/<basename>.json          (latest convenience copy)
    Returns the ticker-scoped path as a string.
    """
    import json
    from pathlib import Path

    outputs_dir = Path(outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    t = (ticker or "").upper().strip()
    scoped = outputs_dir / f"{basename}_{t}.json"
    latest = outputs_dir / f"{basename}.json"

    scoped.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    latest.write_text(scoped.read_text(encoding="utf-8"), encoding="utf-8")
    return str(scoped)
'''.lstrip("\n")


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: can't find {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # 1) Insert helper if missing
    if "def write_ticker_json(" not in src:
        # Put helper after imports if possible
        # Find end of import block (simple heuristic)
        lines = src.splitlines(True)

        insert_at = 0
        # Skip shebang / encoding comments
        i = 0
        while i < len(lines) and (lines[i].startswith("#!") or "coding:" in lines[i] or lines[i].strip() == ""):
            i += 1

        # Move past contiguous import/from blocks and blank lines
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("import ") or s.startswith("from "):
                i += 1
                continue
            # allow blank lines between imports
            if s == "":
                i += 1
                continue
            break

        insert_at = i  # after import region
        lines.insert(insert_at, "\n" + HELPER + "\n\n")
        src = "".join(lines)

    # 2) Replace ANY writes to decision_summary.json with ticker-scoped writer
    # Covers common patterns:
    # - write_json(summary, OUTPUTS / "decision_summary.json")
    # - (OUTPUTS / "decision_summary.json").write_text(...)
    # - json.dump(... open(OUTPUTS / "decision_summary.json", ...))
    # We'll replace the whole *line* whenever it mentions decision_summary.json and is a "write" line.
    out_lines = []
    replaced = 0
    for line in src.splitlines(True):
        if "decision_summary.json" in line:
            # Only replace if it looks like writing (very likely)
            if any(k in line for k in ("write_json", "write_text", "json.dump", "dump(", "open(")):
                indent = re.match(r"\s*", line).group(0)
                out_lines.append(f'{indent}write_ticker_json(OUTPUTS, PRIMARY, "decision_summary", summary)\n')
                replaced += 1
                continue
        out_lines.append(line)

    new_src = "".join(out_lines)

    if replaced == 0:
        # If we didn't find the write line, add a safe fallback near the end of main()
        # This is conservative: we won't guess variable names if "summary" doesn't exist.
        # We just warn clearly.
        TARGET.write_text(new_src, encoding="utf-8")
        raise SystemExit(
            "PATCH PARTIAL: Added helper, but could not auto-find decision_summary.json write line.\n"
            "Tell me and I’ll give you a second autopatch that targets your exact write block."
        )

    TARGET.write_text(new_src, encoding="utf-8")
    print(f"OK ✅ patched {TARGET} (replaced {replaced} decision_summary write line(s)).")


if __name__ == "__main__":
    main()
