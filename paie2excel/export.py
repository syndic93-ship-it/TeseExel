import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ENTETES_ECRITURES = ["Date", "Compte", "Libellé", "Débit", "Crédit", "Référence", "Salarié"]
ENTETES_RECAP = ["Compte", "Libellé", "Total Débit", "Total Crédit"]

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")
MONTANT_FORMAT = "#,##0.00"


def _style_header(worksheet, headers):
    for column, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=1, column=column, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
    worksheet.freeze_panes = "A2"


def _autosize(worksheet):
    for column_cells in worksheet.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(length + 4, 60)


def write_xlsx(ecritures, recap, path, totaux=None):
    path = Path(path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Écritures"
    _style_header(sheet, ENTETES_ECRITURES)
    for row_index, e in enumerate(ecritures, start=2):
        sheet.cell(row=row_index, column=1, value=e.date)
        sheet.cell(row=row_index, column=2, value=e.compte)
        sheet.cell(row=row_index, column=3, value=e.libelle)
        debit_cell = sheet.cell(row=row_index, column=4, value=e.debit or None)
        credit_cell = sheet.cell(row=row_index, column=5, value=e.credit or None)
        debit_cell.number_format = MONTANT_FORMAT
        credit_cell.number_format = MONTANT_FORMAT
        sheet.cell(row=row_index, column=6, value=e.reference)
        sheet.cell(row=row_index, column=7, value=e.salarie or None)
    if totaux:
        total_row = len(ecritures) + 2
        sheet.cell(row=total_row, column=3, value="TOTAL").font = Font(bold=True)
        debit_cell = sheet.cell(row=total_row, column=4, value=totaux[0])
        credit_cell = sheet.cell(row=total_row, column=5, value=totaux[1])
        debit_cell.number_format = MONTANT_FORMAT
        credit_cell.number_format = MONTANT_FORMAT
        debit_cell.font = Font(bold=True)
        credit_cell.font = Font(bold=True)
    _autosize(sheet)

    recap_sheet = workbook.create_sheet("Récap")
    _style_header(recap_sheet, ENTETES_RECAP)
    for row_index, item in enumerate(recap, start=2):
        recap_sheet.cell(row=row_index, column=1, value=item["compte"])
        recap_sheet.cell(row=row_index, column=2, value=item["libelle"])
        debit_cell = recap_sheet.cell(row=row_index, column=3, value=item["debit"] or None)
        credit_cell = recap_sheet.cell(row=row_index, column=4, value=item["credit"] or None)
        debit_cell.number_format = MONTANT_FORMAT
        credit_cell.number_format = MONTANT_FORMAT
    if totaux:
        total_row = len(recap) + 2
        recap_sheet.cell(row=total_row, column=2, value="TOTAL").font = Font(bold=True)
        debit_cell = recap_sheet.cell(row=total_row, column=3, value=totaux[0])
        credit_cell = recap_sheet.cell(row=total_row, column=4, value=totaux[1])
        debit_cell.number_format = MONTANT_FORMAT
        credit_cell.number_format = MONTANT_FORMAT
        debit_cell.font = Font(bold=True)
        credit_cell.font = Font(bold=True)
    _autosize(recap_sheet)

    workbook.save(path)
    return path


def _format_montant_csv(value):
    return f"{value:.2f}".replace(".", ",")


def write_csv(ecritures, path):
    path = Path(path)
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(ENTETES_ECRITURES)
        for e in ecritures:
            writer.writerow([
                e.date, e.compte, e.libelle,
                _format_montant_csv(e.debit) if e.debit else "",
                _format_montant_csv(e.credit) if e.credit else "",
                e.reference, e.salarie,
            ])
    return path


def write_report(path, anomalies, hypotheses, periode, entreprise, totaux):
    path = Path(path)
    lines = [
        "RAPPORT DE CONVERSION PAIE → COMPTABILITÉ",
        "=" * 45,
        f"Entreprise : {entreprise}",
        f"Période : {periode}",
        f"Total débit : {_format_montant_csv(totaux[0])} €",
        f"Total crédit : {_format_montant_csv(totaux[1])} €",
        "",
        "HYPOTHÈSES RETENUES",
        "-" * 20,
    ]
    lines += hypotheses if hypotheses else ["Aucune hypothèse particulière."]
    lines += ["", "ANOMALIES DÉTECTÉES", "-" * 20]
    lines += anomalies if anomalies else ["Aucune anomalie détectée."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
