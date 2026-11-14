import re
from pathlib import Path

from pypdf import PdfReader

PAYROLL_KEYWORDS = (
    "état récapitulatif",
    "etat recapitulatif",
    "récapitulatif de paie",
    "recapitulatif de paie",
    "état de paie",
    "relevé de paie",
    "bulletin de paie",
    "masse salariale",
)

REQUIRED_COLUMNS = ("brut", "cotisation", "net")


def _page_text(page):
    try:
        return page.extract_text(extraction_mode="layout") or ""
    except TypeError:
        return page.extract_text() or ""


def extract_text(pdf_path):
    reader = PdfReader(str(Path(pdf_path)))
    return "\n".join(_page_text(page) for page in reader.pages)


def extract_tables(pdf_path):
    reader = PdfReader(str(Path(pdf_path)))
    tables = []
    current = []
    for page in reader.pages:
        for line in _page_text(page).splitlines():
            cells = [cell.strip() for cell in re.split(r"\s{2,}", line.strip()) if cell.strip()]
            if len(cells) >= 2:
                current.append(cells)
            elif current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def is_payroll_summary(text):
    lowered = text.lower()
    if not any(keyword in lowered for keyword in PAYROLL_KEYWORDS):
        return False
    return all(column in lowered for column in REQUIRED_COLUMNS)