import re
from dataclasses import dataclass, field

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}

NUMBER_RE = re.compile(r"^-?\s?\d[\d\s.,]*\d$|^-?\s?\d$")

RUBRIQUE_HEADERS = ("rubrique", "libellé", "libelle", "désignation", "designation", "nature")
MONTANT_HEADERS = ("montant", "total", "euro", "€")
SALARIE_HEADERS = ("salarié", "salarie", "nom", "matricule", "collaborateur")


@dataclass
class LignePaie:
    rubrique: str
    montant: float
    salarie: str = ""


@dataclass
class PaieParsee:
    periode: str = "[MISSING_DATA]"
    entreprise: str = "[MISSING_DATA]"
    lignes: list = field(default_factory=list)
    totaux_brut: float = 0.0
    totaux_cotisations: float = 0.0
    totaux_net: float = 0.0


def parse_number(raw):
    if raw is None:
        return None
    text = str(raw).strip().replace("\u00a0", " ").replace("€", "").strip()
    if not text:
        return None
    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = text.strip("()-").strip()
    candidate = ("-" if negative else "") + text
    if not NUMBER_RE.match(candidate):
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        head, _, tail = text.rpartition(",")
        if re.match(r"^\d{1,3}([ .]\d{3})*$", head) and len(tail) == 2:
            text = head.replace(" ", "").replace(".", "") + "." + tail
        else:
            text = text.replace(",", ".")
    text = text.replace(" ", "")
    try:
        value = float(text)
    except ValueError:
        return None
    return -value if negative else value


def _parse_periode(text):
    lowered = text.lower()
    match = re.search(r"(p[ée]riode|mois)\s*:?\s*([a-zéû]+)\s*(\d{4})", lowered)
    if match:
        month = MONTHS_FR.get(match.group(2))
        if month:
            return f"{match.group(2).capitalize()} {match.group(3)}"
    match = re.search(r"\b(\d{2})/(\d{4})\b", text)
    if match:
        month = int(match.group(1))
        if 1 <= month <= 12:
            names = sorted(
                (k for k, v in MONTHS_FR.items() if v == month),
                key=lambda k: ("é" in k or "û" in k),
            )
            return f"{names[0].capitalize()} {match.group(2)}"
    return "[MISSING_DATA]"


def _parse_entreprise(text):
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^(entreprise|soci[ée]t[ée]|raison sociale)\s*:?\s*(.+)$", stripped, re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return "[MISSING_DATA]"


def _normalize(header):
    return header.strip().lower()


def _parse_table(table, paie):
    if not table:
        return
    header = [_normalize(cell) for cell in table[0]]
    salarie_idx = next((i for i, h in enumerate(header) if h in SALARIE_HEADERS), None)
    rubrique_idx = next((i for i, h in enumerate(header) if h in RUBRIQUE_HEADERS), None)
    montant_idx = next((i for i, h in enumerate(header) if h in MONTANT_HEADERS), None)
    if rubrique_idx is not None and montant_idx is not None:
        for row in table[1:]:
            if len(row) <= max(rubrique_idx, montant_idx):
                continue
            montant = parse_number(row[montant_idx])
            rubrique = row[rubrique_idx].strip()
            if montant is None or not rubrique:
                continue
            if rubrique.lower() in ("total", "totaux", "total général", "total general"):
                continue
            paie.lignes.append(LignePaie(rubrique=rubrique, montant=montant))
        return
    if salarie_idx is not None:
        amount_columns = [
            (i, header[i]) for i in range(len(header))
            if i != salarie_idx and parse_number(header[i]) is None and any(
                token in header[i] for token in ("brut", "cotisation", "net", "charge", "salaire", "montant")
            )
        ]
        if not amount_columns:
            amount_columns = [(i, header[i]) for i in range(len(header)) if i != salarie_idx]
        for row in table[1:]:
            if len(row) <= salarie_idx:
                continue
            salarie = row[salarie_idx].strip()
            if not salarie or salarie.lower() in ("total", "totaux"):
                continue
            for idx, col_header in amount_columns:
                if idx >= len(row):
                    continue
                montant = parse_number(row[idx])
                if montant is None:
                    continue
                rubrique = col_header.capitalize() if col_header else "[MISSING_DATA]"
                paie.lignes.append(LignePaie(rubrique=rubrique, montant=montant, salarie=salarie))
        return
    for row in table:
        numeric = [(i, parse_number(cell)) for i, cell in enumerate(row)]
        numeric = [(i, v) for i, v in numeric if v is not None]
        if len(numeric) != 1:
            continue
        idx, montant = numeric[0]
        rubrique = " ".join(cell for i, cell in enumerate(row[:idx]) if cell).strip()
        if not rubrique or rubrique.lower() in ("total", "totaux"):
            continue
        paie.lignes.append(LignePaie(rubrique=rubrique, montant=montant))


def parse_paies(text, tables):
    paie = PaieParsee(periode=_parse_periode(text), entreprise=_parse_entreprise(text))
    for table in tables:
        _parse_table(table, paie)
    if not paie.lignes:
        for line in text.splitlines():
            parts = re.split(r"\s{2,}|\t", line.strip())
            if len(parts) == 2:
                montant = parse_number(parts[1])
                if montant is not None and parts[0].strip():
                    paie.lignes.append(LignePaie(rubrique=parts[0].strip(), montant=montant))
    for ligne in paie.lignes:
        low = ligne.rubrique.lower()
        if any(token in low for token in ("brut", "salaire", "heures sup", "prime", "indemnite")):
            paie.totaux_brut += ligne.montant
        if "cotisation" in low:
            paie.totaux_cotisations += ligne.montant
        if "net" in low:
            paie.totaux_net += ligne.montant
    return paie
