from pathlib import Path

P = Path("scripts/build_super_memo.py")
lines = P.read_text(encoding="utf-8").splitlines(True)

# If we see plain-English sentences living in the file (not inside quotes),
# Python will crash. We'll remove the offending block starting at that sentence
# until we hit a real code-looking line again.

START_TRIGGERS = (
    "This means GM sold LESS than it sold the year before.",
    "This means",
    "Okay. Imagine",
    "Revenue growth =",
)

CODE_PREFIXES = (
    "import ", "from ",
    "def ", "class ",
    "if ", "for ", "while ", "try:", "except", "return ",
    "md.append", "md_path", "doc", "print(", "#",
)

out = []
skipping = False
skipped = 0

for ln in lines:
    s = ln.strip()

    # Start skipping if we hit any of the known “naked story text” triggers
    if (not skipping) and s and any(s.startswith(t) for t in START_TRIGGERS):
        skipping = True
        skipped += 1
        continue

    if skipping:
        # Stop skipping once we see something that looks like actual Python code again
        if any(ln.lstrip().startswith(p) for p in CODE_PREFIXES):
            skipping = False
            out.append(ln)
        else:
            skipped += 1
        continue

    out.append(ln)

P.write_text("".join(out), encoding="utf-8")
print(f"✅ Removed naked story text lines: {skipped}")
