from pathlib import Path

P = Path("scripts/build_super_memo.py")
lines = P.read_text(encoding="utf-8").splitlines(True)

def is_orphan_closer(s: str) -> bool:
    t = s.strip()
    # closers that are commonly left alone after bad edits
    return t in (")", "),", "]", "],", "}", "},")

out = []
removed = 0

# remove orphan closer lines ONLY when the previous meaningful line
# does NOT look like it is waiting for a closer (best-effort heuristic)
def prev_meaningful(out_lines):
    for k in range(len(out_lines)-1, -1, -1):
        t = out_lines[k].strip()
        if t == "" or t.startswith("#"):
            continue
        return t
    return ""

for ln in lines:
    if is_orphan_closer(ln):
        prev = prev_meaningful(out)
        # If previous line already ended with an opener, keep the closer
        # else remove it (this is the common broken case)
        if prev.endswith(("(", "[", "{")):
            out.append(ln)
        else:
            removed += 1
            continue
    else:
        out.append(ln)

P.write_text("".join(out), encoding="utf-8")
print(f"✅ Removed orphan closers: {removed}")
