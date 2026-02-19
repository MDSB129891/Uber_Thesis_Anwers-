from pathlib import Path
import re

P = Path("scripts/build_super_memo.py")
lines = P.read_text(encoding="utf-8").splitlines(True)

out = []
i = 0
added = 0

def indent_level(s: str) -> int:
    return len(s) - len(s.lstrip(" "))

BLOCK_START = re.compile(r'^\s*(if|elif|else|for|while|try|except|finally|with|def|class)\b.*:\s*$')

while i < len(lines):
    ln = lines[i]
    out.append(ln)

    if BLOCK_START.match(ln):
        base = indent_level(ln)
        j = i + 1

        # skip blank lines and comments when checking if block has content
        while j < len(lines) and (lines[j].strip() == "" or lines[j].lstrip().startswith("#")):
            out.append(lines[j])
            j += 1

        # if file ends right after a block start, or next meaningful line is not indented -> empty block
        if j >= len(lines) or indent_level(lines[j]) <= base:
            out.append(" " * (base + 4) + "pass\n")
            added += 1

        i = j
        continue

    i += 1

P.write_text("".join(out), encoding="utf-8")
print(f"✅ Inserted pass into empty blocks: {added}")
