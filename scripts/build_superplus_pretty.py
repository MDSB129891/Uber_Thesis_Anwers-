from pathlib import Path
import subprocess
def _write_pdf_from_html(html_path: Path, pdf_path: Path):
    """
    PDF rendering strategy (Mac friendly):
    1) Try Chrome/Chromium headless print-to-pdf (best looking, no GTK deps)
    2) Try WeasyPrint (if installed + deps present)
    """
    # --- 1) Chrome headless ---
    chrome_bins = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ]
    for b in chrome_bins:
        try:
            cmd = [
                b,
                "--headless=new",
                "--disable-gpu",
                f"--print-to-pdf={str(pdf_path)}",
                str(html_path),
            ]
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if r.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
                return
        except FileNotFoundError:
            continue

    # --- 2) WeasyPrint fallback ---
    try:
        import weasyprint
        weasyprint.HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return
    except Exception as e:
        raise RuntimeError(f"PDF export failed (Chrome + WeasyPrint). Last error: {e}")

    # --- 2) WeasyPrint fallback ---
    try:
        import weasyprint
        weasyprint.HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        return
    except Exception as e:
        raise RuntimeError(f"PDF export failed (Chrome + WeasyPrint). Last error: {e}")