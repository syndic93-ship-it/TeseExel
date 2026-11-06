import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent.parent / "mapping_default.csv"

COMPTE_NON_MAPPE = "[NON_MAPPÉ]"


@dataclass
class MappingResult:
    compte: str
    sens: str
    libelle: str
    pattern: str
    contrepartie: str = ""
    ambigu: bool = False


def _normalize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"[^a-z0-9 ]", " ", text).strip()


def load_mapping(path=None):
    path = Path(path) if path else DEFAULT_MAPPING_PATH
    rules = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            pattern = _normalize(row["pattern"])
            if pattern:
                rules.append({
                    "pattern": pattern,
                    "compte": row["compte"].strip(),
                    "sens": row["sens"].strip().lower(),
                    "libelle": row["libelle"].strip(),
                    "contrepartie": (row.get("contrepartie") or "").strip(),
                })
    rules.sort(key=lambda r: len(r["pattern"]), reverse=True)
    return rules


def map_rubrique(rubrique, rules):
    normalized = _normalize(rubrique)
    matches = [rule for rule in rules if rule["pattern"] in normalized]
    if not matches:
        return MappingResult(
            compte=COMPTE_NON_MAPPE, sens="debit", libelle=rubrique,
            pattern="", ambigu=False,
        )
    best = matches[0]
    best_len = len(best["pattern"])
    distinct = {(m["compte"], m["sens"]) for m in matches if len(m["pattern"]) == best_len}
    return MappingResult(
        compte=best["compte"], sens=best["sens"], libelle=best["libelle"],
        pattern=best["pattern"], contrepartie=best["contrepartie"],
        ambigu=len(distinct) > 1,
    )
