from pathlib import Path

import pdfplumber

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


def extract_text(pdf_path):
    path = Path(pdf_path)
    with pdfplumber.open(path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def extract_tables(pdf_path):
    path = Path(pdf_path)
    tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                cleaned = [
                    [" ".join(str(cell or "").split()) for cell in row]
                    for row in table
                    if any(str(cell or "").strip() for cell in row)
                ]
                if cleaned:
                    tables.append(cleaned)
    return tables


def is_payroll_summary(text):
    lowered = text.lower()
    if not any(keyword in lowered for keyword in PAYROLL_KEYWORDS):
        return False
    return all(column in lowered for column in REQUIRED_COLUMNS)
