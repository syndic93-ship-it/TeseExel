from openpyxl import load_workbook

from paie2excel.cli import main
from paie2excel.extraction import is_payroll_summary, extract_text


def test_detecte_etat_paie(sample_pdf, not_payroll_pdf):
    assert is_payroll_summary(extract_text(sample_pdf))
    assert not is_payroll_summary(extract_text(not_payroll_pdf))


def test_cli_end_to_end(sample_pdf, tmp_path):
    output = tmp_path / "sortie.xlsx"
    rapport = tmp_path / "rapport.txt"
    csv = tmp_path / "sortie.csv"
    code = main([
        str(sample_pdf), "-o", str(output), "--date", "04/11/2026",
        "--reference", "Paie_Oct26_001", "--rapport", str(rapport), "--csv", str(csv),
    ])
    assert code == 0
    assert output.is_file() and rapport.is_file() and csv.is_file()

    workbook = load_workbook(output)
    assert workbook.sheetnames == ["Écritures", "Récap"]
    sheet = workbook["Écritures"]
    headers = [cell.value for cell in sheet[1]]
    assert headers == ["Date", "Compte", "Libellé", "Débit", "Crédit", "Référence", "Salarié"]
    lignes = [l for l in sheet.iter_rows(min_row=2, values_only=True) if l[1]]
    assert len(lignes) == 5
    assert all(l[0] == "04/11/2026" for l in lignes)
    assert all(l[5] == "Paie_Oct26_001" for l in lignes)
    debit = sum(l[3] or 0 for l in lignes)
    credit = sum(l[4] or 0 for l in lignes)
    assert abs(debit - credit) < 0.01

    recap = workbook["Récap"]
    comptes = {row[0]: (row[2] or 0, row[3] or 0) for row in recap.iter_rows(min_row=2, values_only=True) if row[0]}
    assert comptes["641"] == (50000.0, 0.0)
    assert comptes["645"] == (21000.0, 0.0)
    assert comptes["431"][1] == 32000.0
    assert comptes["421"][1] == 39000.0

    contenu_csv = csv.read_text(encoding="utf-8-sig")
    assert ";" in contenu_csv.splitlines()[0]
    assert "50000,00" in contenu_csv

    texte = rapport.read_text(encoding="utf-8")
    assert "Octobre 2026" in texte
    assert "ANOMALIES" in texte


def test_cli_rejette_non_paie(not_payroll_pdf, tmp_path, capsys):
    code = main([str(not_payroll_pdf), "-o", str(tmp_path / "x.xlsx")])
    assert code == 2
    assert "pas être un état récapitulatif" in capsys.readouterr().err


def test_cli_pdf_par_salarie(sample_pdf_salaries, tmp_path):
    output = tmp_path / "salaries.xlsx"
    code = main([str(sample_pdf_salaries), "-o", str(output), "--par-salarie"])
    assert code == 0
    workbook = load_workbook(output)
    sheet = workbook["Écritures"]
    salaries = [row[6] for row in sheet.iter_rows(min_row=2, values_only=True) if row[6]]
    assert "Dupont J." in salaries and "Martin L." in salaries
