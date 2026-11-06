import argparse
import sys
from pathlib import Path

from paie2excel.ecritures import generer_ecritures, recapituler
from paie2excel.export import write_csv, write_report, write_xlsx
from paie2excel.extraction import extract_tables, extract_text, is_payroll_summary
from paie2excel.mapping import load_mapping
from paie2excel.parsing import parse_paies
from paie2excel.validation import valider


def build_parser():
    parser = argparse.ArgumentParser(
        prog="paie2excel",
        description="Convertit un état récapitulatif mensuel de paie (PDF) en écritures comptables XLSX.",
    )
    parser.add_argument("pdf", help="Chemin du fichier PDF (état récapitulatif de paie)")
    parser.add_argument("-o", "--output", help="Fichier XLSX de sortie (défaut : <pdf>.xlsx)")
    parser.add_argument("--csv", help="Export CSV additionnel (séparateur ';', décimales à virgule)")
    parser.add_argument("--mapping", help="Fichier CSV de mapping personnalisé (pattern;compte;sens;libelle)")
    parser.add_argument("--date", help="Date des écritures au format JJ/MM/AAAA (défaut : fin de période)")
    parser.add_argument("--reference", help="Référence pièce (défaut : Paie_<Période>)")
    parser.add_argument("--par-salarie", action="store_true", help="Détail des écritures par salarié")
    parser.add_argument("--rapport", help="Fichier de rapport texte (anomalies et hypothèses)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"Erreur : fichier introuvable : {pdf_path}", file=sys.stderr)
        return 1
    try:
        text = extract_text(pdf_path)
        tables = extract_tables(pdf_path)
    except Exception as exc:
        print(f"Erreur de lecture du PDF : {exc}", file=sys.stderr)
        return 1
    if not is_payroll_summary(text):
        print(
            "Le PDF ne semble pas être un état récapitulatif de paie. "
            "Veuillez vérifier le document (attendu : tableau avec colonnes "
            "'Salarié', 'Brut', 'Cotisations', etc.).",
            file=sys.stderr,
        )
        return 2
    paie = parse_paies(text, tables)
    if not paie.lignes:
        print("Aucune ligne de paie détectée dans le PDF.", file=sys.stderr)
        return 2
    rules = load_mapping(args.mapping)
    ecritures, hypotheses = generer_ecritures(
        paie, rules, date_str=args.date, reference=args.reference, par_salarie=args.par_salarie
    )
    anomalies, total_debit, total_credit = valider(ecritures, paie)
    recap = recapituler(ecritures)
    output = Path(args.output) if args.output else pdf_path.with_suffix(".xlsx")
    write_xlsx(ecritures, recap, output, totaux=(total_debit, total_credit))
    if args.csv:
        write_csv(ecritures, args.csv)
    report_path = Path(args.rapport) if args.rapport else output.with_suffix(".rapport.txt")
    write_report(report_path, anomalies, hypotheses, paie.periode, paie.entreprise, (total_debit, total_credit))
    print(f"XLSX généré : {output}")
    print(f"Rapport généré : {report_path}")
    print(f"Écritures : {len(ecritures)} | Débit total : {total_debit:.2f} | Crédit total : {total_credit:.2f}")
    if anomalies:
        print(f"Anomalies ({len(anomalies)}) :", file=sys.stderr)
        for anomalie in anomalies:
            print(f"  - {anomalie}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
