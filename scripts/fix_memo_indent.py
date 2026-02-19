from pathlib import Path

p = Path("scripts/build_investment_memo.py")
lines = p.read_text(encoding="utf-8").splitlines()

fixed = []
for ln in lines:
    # Remove the broken auto-render line if it exists
    if "_render_md_lines_to_docx(doc, md" in ln:
        continue
    fixed.append(ln)

p.write_text("\n".join(fixed) + "\n", encoding="utf-8")
print("Stage 1 cleanup done")

# Now insert clean renderer near top of file
txt = p.read_text(encoding="utf-8")

helper = """

def _render_md_lines_to_docx(doc, lines, *, doc_add_h1, doc_add_h2, doc_add_h3, doc_add_lines):
    for raw in lines:
        line = (raw or "").rstrip()
        if not line.strip():
            doc.add_paragraph("")
            continue

        if line.startswith("### "):
            doc_add_h3(doc, line[4:].strip())
            continue
        if line.startswith("## "):
            doc_add_h2(doc, line[3:].strip())
            continue
        if line.startswith("# "):
            doc_add_h1(doc, line[2:].strip())
            continue

        if line.startswith("- "):
            doc_add_lines(doc, "• " + line[2:].strip())
            continue

        doc_add_lines(doc, line)
"""

if "_render_md_lines_to_docx" not in txt:
    idx = txt.find("def main(")
    txt = txt[:idx] + helper + "\n\n" + txt[idx:]

p.write_text(txt, encoding="utf-8")
print("Stage 2 helper inserted cleanly")
