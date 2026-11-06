from paie2excel.parsing import parse_number, parse_paies
from paie2excel.extraction import extract_tables, extract_text


def test_parse_number_formats_fr():
    assert parse_number("1 234,56") == 1234.56
    assert parse_number("1.234,56") == 1234.56
    assert parse_number("1234.56") == 1234.56
    assert parse_number("-500,00") == -500.0
    assert parse_number("(250,00)") == -250.0
    assert parse_number("3000") == 3000.0
    assert parse_number("abc") is None
    assert parse_number("") is None


def test_parse_paies_recap(sample_pdf):
    text = extract_text(sample_pdf)
    tables = extract_tables(sample_pdf)
    paie = parse_paies(text, tables)
    assert paie.periode == "Octobre 2026"
    assert paie.entreprise == "ACME SAS"
    rubriques = {ligne.rubrique: ligne.montant for ligne in paie.lignes}
    assert rubriques["Salaire brut"] == 50000.0
    assert rubriques["Net à payer"] == 39000.0
    assert paie.totaux_brut == 50000.0
    assert paie.totaux_net == 39000.0


def test_parse_paies_par_salarie(sample_pdf_salaries):
    text = extract_text(sample_pdf_salaries)
    tables = extract_tables(sample_pdf_salaries)
    paie = parse_paies(text, tables)
    assert len(paie.lignes) == 6
    dupont = [l for l in paie.lignes if l.salarie == "Dupont J."]
    assert len(dupont) == 3
    assert any(l.rubrique.lower() == "brut" and l.montant == 3000.0 for l in dupont)
