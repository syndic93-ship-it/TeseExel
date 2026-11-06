from paie2excel.ecritures import generer_ecritures, recapituler
from paie2excel.mapping import COMPTE_NON_MAPPE, load_mapping, map_rubrique
from paie2excel.parsing import LignePaie, PaieParsee
from paie2excel.validation import valider


def _paie(lignes):
    paie = PaieParsee(periode="Octobre 2026", entreprise="ACME SAS")
    paie.lignes = lignes
    return paie


def test_mapping_defaut():
    rules = load_mapping()
    assert map_rubrique("Salaire brut", rules).compte == "641"
    assert map_rubrique("Cotisations Urssaf", rules).compte == "431"
    assert map_rubrique("Mutuelle patronale", rules).compte == "647"
    assert map_rubrique("Net à payer", rules).compte == "421"
    assert map_rubrique("Rubrique inconnue xyz", rules).compte == COMPTE_NON_MAPPE


def test_ecritures_equilibrees():
    rules = load_mapping()
    paie = _paie([
        LignePaie("Salaire brut", 5000.0),
        LignePaie("Cotisations salariales", 1100.0),
        LignePaie("Net à payer", 3900.0),
    ])
    ecritures, hypotheses = generer_ecritures(paie, rules, date_str="04/11/2026", reference="Paie_Oct26_001")
    assert all(e.date == "04/11/2026" for e in ecritures)
    assert all(e.reference == "Paie_Oct26_001" for e in ecritures)
    anomalies, debit, credit = valider(ecritures)
    assert not anomalies
    assert debit == credit == 5000.0
    recap = recapituler(ecritures)
    comptes = {r["compte"]: r for r in recap}
    assert comptes["641"]["debit"] == 5000.0
    assert comptes["421"]["credit"] == 3900.0
    assert comptes["431"]["credit"] == 1100.0


def test_contrepartie_charges_patronales():
    rules = load_mapping()
    paie = _paie([
        LignePaie("Salaire brut", 5000.0),
        LignePaie("Charges patronales", 2000.0),
        LignePaie("Cotisations salariales", 1100.0),
        LignePaie("Net à payer", 3900.0),
    ])
    ecritures, _ = generer_ecritures(paie, rules)
    assert any(e.compte == "645" and e.debit == 2000.0 for e in ecritures)
    assert any(e.compte == "431" and e.credit == 2000.0 for e in ecritures)
    anomalies, debit, credit = valider(ecritures)
    assert not anomalies
    assert debit == credit == 7000.0


def test_montant_negatif_compte_421():
    rules = load_mapping()
    paie = _paie([
        LignePaie("Salaire brut", 3000.0),
        LignePaie("Salaire brut", -200.0),
        LignePaie("Cotisations salariales", 600.0),
        LignePaie("Net à payer", 2200.0),
    ])
    ecritures, hypotheses = generer_ecritures(paie, rules)
    neg = [e for e in ecritures if e.credit == 200.0]
    assert len(neg) == 1 and neg[0].compte == "421"
    assert any("trop-perçu" in h for h in hypotheses)
    anomalies, debit, credit = valider(ecritures)
    assert not anomalies


def test_rubrique_inconnue_signalee():
    rules = load_mapping()
    paie = _paie([LignePaie("Avantage en nature mystère", 100.0)])
    ecritures, hypotheses = generer_ecritures(paie, rules)
    assert ecritures[0].compte == COMPTE_NON_MAPPE
    assert any("non mappée" in h for h in hypotheses)
    anomalies, _, _ = valider(ecritures)
    assert any("[NON" in a or "non renseigné" in a for a in anomalies)
