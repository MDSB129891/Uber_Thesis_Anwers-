from __future__ import annotations

from pathlib import Path
import re

P = Path("scripts/build_investment_memo.py")
txt = P.read_text(encoding="utf-8")

# 1) Add a small helper that converts markdown-ish lines into real Word headings
if "def _render_md_lines_to_docx(" not in txt:
    insert_point = txt.find("def main(")
    if insert_point == -1:
        raise SystemExit("Could not find def main(...) in build_investment_memo.py")

    helper = r'''
def _render_md_lines_to_docx(doc, lines, *, doc_add_h1, doc_add_h2, doc_add_h3, doc_add_lines):
    """
    Takes a list of markdown-ish lines and renders them to docx WITHOUT showing ##/###.
    """
    for raw in lines:
        line = (raw or "").rstrip()
        if not line.strip():
            doc.add_paragraph("")
            continue

        # Headings
        if line.startswith("### "):
            doc_add_h3(doc, line[4:].strip())
            continue
        if line.startswith("## "):
            doc_add_h2(doc, line[3:].strip())
            continue
        if line.startswith("# "):
            doc_add_h1(doc, line[2:].strip())
            continue

        # Bullet normalization
        if line.startswith("- "):
            # keep as simple bullet-like line
            doc_add_lines(doc, "• " + line[2:].strip())
            continue

        # Strip accidental markdown markers inside paragraphs
        line = re.sub(r"^#+\s*", "", line)

        doc_add_lines(doc, line)
'''
    txt = txt[:insert_point] + helper + "\n\n" + txt[insert_point:]


# 2) Ensure the thesis section is never blank in the DOCX:
# We'll find a spot where the docx "The thesis (Base case)" is written and enforce description output.
# If your file doesn't have that exact string, we patch the first "The thesis" header block we can.
patterns = [
    r'doc_add_h1\(doc,\s*"The thesis \(Base case\)"\)\s*',
    r'doc_add_h2\(doc,\s*"The thesis \(Base case\)"\)\s*',
    r'doc_add_h1\(doc,\s*"The thesis"\)\s*',
    r'doc_add_h2\(doc,\s*"The thesis"\)\s*',
]

patched_thesis = False
for pat in patterns:
    m = re.search(pat, txt)
    if not m:
        continue

    # Insert right AFTER the heading call.
    insertion = r'''
    # --- ensure thesis text is printed (never blank) ---
    base_thesis = (suite.get("base", {}) or {}).get("thesis", {}) or {}
    thesis_title = base_thesis.get("name") or base_thesis.get("title") or ""
    thesis_desc = base_thesis.get("description") or ""

    if thesis_title:
        doc_add_lines(doc, f"Thesis: {thesis_title}")
    if thesis_desc:
        doc_add_lines(doc, thesis_desc)
    else:
        doc_add_lines(doc, "(No thesis description was provided. Add 'description' to the thesis JSON.)")
'''
    txt = txt[:m.end()] + insertion + txt[m.end():]
    patched_thesis = True
    break

if not patched_thesis:
    print("WARN: Could not find thesis heading block to patch. (Not fatal.)")

# 3) Replace any loop that dumps md lines into docx with our renderer
# Common anti-pattern: for line in md: doc_add_lines(doc, line)
# We'll patch the first such loop we find.
loop_pat = r'for\s+line\s+in\s+md:\s*\n\s*doc_add_lines\(doc,\s*line\)\s*'
if re.search(loop_pat, txt):
    txt = re.sub(
        loop_pat,
        " _render_md_lines_to_docx(doc, md, doc_add_h1=doc_add_h1, doc_add_h2=doc_add_h2, doc_add_h3=doc_add_h3, doc_add_lines=doc_add_lines)\n",
        txt,
        count=1,
    )

P.write_text(txt, encoding="utf-8")
print("DONE ✅ Patched build_investment_memo.py (thesis section + markdown -> Word headings)")
