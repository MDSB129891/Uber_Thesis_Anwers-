from pathlib import Path
import re

P = Path("scripts/build_super_memo.py")
lines = P.read_text(encoding="utf-8").splitlines(True)

CODE_PREFIXES = (
    "import ", "from ",
    "def ", "class ",
    "if ", "elif ", "else:",
    "for ", "while ",
    "try:", "except", "finally:",
    "with ",
    "return ", "pass", "break", "continue",
    "print(", "#",
    "md.append", "md_path", "doc", "ap.", "args", "main(",
)

def looks_like_code(ln: str) -> bool:
    s = ln.lstrip()
    if not s.strip():
        return True  # blank line OK
    if s.startswith(CODE_PREFIXES):
        return True
    if s.startswith(("'", '"', "f'", 'f"', "r'", 'r"', "fr'", 'fr"', "rf'", 'rf"')):
        return True  # string literal line OK
    if "=" in s and not s.strip().startswith("=="):
        return True  # assignments OK
    if s.strip().endswith(":"):
        return True  # blocks OK
    if s.strip().startswith((")", "]", "}", ",")):
        return True  # closers OK
    return False

removed = 0
out = []

for ln in lines:
    s = ln.lstrip()

    # If line starts with a letter (plain English vibe) AND does NOT look like Python code -> remove it
    if re.match(r"^[A-Za-z]", s) and not looks_like_code(ln):
        removed += 1
        continue

    out.append(ln)

P.write_text("".join(out), encoding="utf-8")
print(f"✅ Removed naked English lines: {removed}")
