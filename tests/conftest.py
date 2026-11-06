import sys
from pathlib import Path

import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _build_pdf(path, rows, title="État récapitulatif mensuel de paie"):
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Entreprise : ACME SAS", styles["Normal"]),
        Paragraph("Période : Octobre 2026", styles["Normal"]),
        Paragraph(title, styles["Heading1"]),
    ]
    data = [["Rubrique", "Montant"]] + rows
    table = Table(data, colWidths=[300, 150])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elements.append(table)
    doc.build(elements)


@pytest.fixture
def sample_pdf(tmp_path):
    path = tmp_path / "paie_oct2026.pdf"
    _build_pdf(path, [
        ["Salaire brut", "50 000,00"],
        ["Cotisations salariales", "11 000,00"],
        ["Net à payer", "39 000,00"],
        ["Charges patronales", "21 000,00"],
    ])
    return path


@pytest.fixture
def sample_pdf_salaries(tmp_path):
    path = tmp_path / "paie_salaries.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Entreprise : ACME SAS", styles["Normal"]),
        Paragraph("Période : Octobre 2026", styles["Normal"]),
        Paragraph("État récapitulatif mensuel de paie", styles["Heading1"]),
    ]
    data = [
        ["Salarié", "Brut", "Cotisations salariales", "Net à payer"],
        ["Dupont J.", "3 000,00", "660,00", "2 340,00"],
        ["Martin L.", "2 500,00", "550,00", "1 950,00"],
    ]
    table = Table(data, colWidths=[150, 100, 150, 120])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    elements.append(table)
    doc.build(elements)
    return path


@pytest.fixture
def not_payroll_pdf(tmp_path):
    path = tmp_path / "facture.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawString(100, 750, "Facture n° 2026-001")
    c.drawString(100, 730, "Client : Société Exemple")
    c.drawString(100, 710, "Montant HT : 1 200,00 EUR")
    c.save()
    return path
