from collections import OrderedDict
from dataclasses import dataclass

from paie2excel.mapping import COMPTE_NON_MAPPE, map_rubrique

COMPTE_TROP_PERCU = "421"


@dataclass
class Ecriture:
    date: str
    compte: str
    libelle: str
    debit: float
    credit: float
    reference: str
    salarie: str = ""


def _default_date(periode):
    from paie2excel.parsing import MONTHS_FR
    import calendar
    import re
    match = re.search(r"([a-zéû]+)\s*(\d{4})", periode.lower())
    if match:
        month = MONTHS_FR.get(match.group(1))
        year = int(match.group(2))
        if month:
            last_day = calendar.monthrange(year, month)[1]
            return f"{last_day:02d}/{month:02d}/{year}"
    from datetime import date
    today = date.today()
    return today.strftime("%d/%m/%Y")


def _normalize_date(raw, periode):
    import re
    from datetime import datetime
    if not raw:
        return _default_date(periode)
    match = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$", raw.strip())
    if not match:
        raise ValueError(f"Date invalide (attendu JJ/MM/AAAA) : {raw}")
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return datetime(year, month, day).strftime("%d/%m/%Y")


def generer_ecritures(paie, rules, date_str=None, reference="", par_salarie=False):
    date = _normalize_date(date_str, paie.periode)
    if not reference:
        reference = f"Paie_{paie.periode.replace(' ', '_')}"
    ecritures = []
    hypotheses = []
    for ligne in paie.lignes:
        result = map_rubrique(ligne.rubrique, rules)
        if result.ambigu:
            hypotheses.append(
                f"Rubrique ambiguë '{ligne.rubrique}' : plusieurs comptes possibles, "
                f"'{result.compte}' retenu."
            )
        if result.compte == COMPTE_NON_MAPPE:
            hypotheses.append(
                f"Rubrique non mappée '{ligne.rubrique}' : compte {COMPTE_NON_MAPPE}, "
                f"à compléter via un fichier de mapping."
            )
        compte = result.compte
        debit = credit = 0.0
        montant = ligne.montant
        if montant < 0:
            compte = COMPTE_TROP_PERCU
            credit = abs(montant)
            hypotheses.append(
                f"Montant négatif sur '{ligne.rubrique}' ({montant}) : comptabilisé au compte "
                f"{COMPTE_TROP_PERCU} (trop-perçu)."
            )
        elif result.sens == "debit":
            debit = montant
        else:
            credit = montant
        libelle = result.libelle if result.compte != COMPTE_NON_MAPPE else ligne.rubrique
        if ligne.salarie and par_salarie:
            libelle = f"{libelle} - {ligne.salarie}"
        ecritures.append(Ecriture(
            date=date, compte=compte, libelle=libelle,
            debit=round(debit, 2), credit=round(credit, 2),
            reference=reference, salarie=ligne.salarie if par_salarie else "",
        ))
        if result.contrepartie and montant > 0:
            contre_debit = montant if result.sens == "credit" else 0.0
            contre_credit = montant if result.sens == "debit" else 0.0
            ecritures.append(Ecriture(
                date=date, compte=result.contrepartie, libelle=result.libelle,
                debit=round(contre_debit, 2), credit=round(contre_credit, 2),
                reference=reference, salarie=ligne.salarie if par_salarie else "",
            ))
    return ecritures, hypotheses


def recapituler(ecritures):
    recap = OrderedDict()
    for ecriture in ecritures:
        entry = recap.setdefault(ecriture.compte, {"libelle": ecriture.libelle, "debit": 0.0, "credit": 0.0})
        entry["debit"] += ecriture.debit
        entry["credit"] += ecriture.credit
    return [
        {"compte": compte, "libelle": values["libelle"],
         "debit": round(values["debit"], 2), "credit": round(values["credit"], 2)}
        for compte, values in recap.items()
    ]
