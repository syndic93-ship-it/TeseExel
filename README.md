# paie2excel

Outil de conversion d'**états récapitulatifs mensuels de paie (PDF)** en **écritures comptables structurées pour Excel (XLSX / CSV)**.

## Fonctionnement

1. **Détection** : vérifie que le PDF est bien un état récapitulatif de paie (mots-clés + colonnes attendues : brut, cotisations, net). Sinon, rejet avec code de sortie `2`.
2. **Extraction** : lecture du texte et des tableaux via `pdfplumber`.
3. **Parsing** : période, entreprise, lignes de paie (mode tableau « Rubrique | Montant » ou mode par salarié « Salarié | Brut | Cotisations | Net »).
4. **Mapping comptable** : chaque rubrique est associée à un compte du plan comptable français (fichier `mapping_default.csv`, personnalisable via `--mapping`). Les charges patronales génèrent automatiquement leur contrepartie au crédit.
5. **Validation** : équilibre débit = crédit, cohérence `net = brut − cotisations salariales`, détection des rubriques non mappées (`[NON_MAPPÉ]`) et des montants négatifs (trop-perçus → compte `421`).
6. **Export** : XLSX avec feuilles **Écritures** et **Récap**, CSV optionnel (`;`, décimales à virgule, UTF-8 BOM), et rapport texte listant hypothèses et anomalies.

## Installation

```bash
pip install -r requirements.txt
# ou en package installable :
pip install .
```

## Utilisation

```bash
paie2excel etat_paie_oct2026.pdf \
  -o ecritures_oct2026.xlsx \
  --date 04/11/2026 \
  --reference Paie_Oct26_001 \
  --csv ecritures_oct2026.csv \
  --rapport rapport_oct2026.txt
```

Options :

| Option | Description |
|---|---|
| `-o/--output` | Fichier XLSX de sortie (défaut : `<pdf>.xlsx`) |
| `--csv` | Export CSV additionnel |
| `--mapping` | CSV personnalisé `pattern;compte;sens;libelle;contrepartie` |
| `--date` | Date des écritures `JJ/MM/AAAA` (défaut : dernier jour de la période) |
| `--reference` | Référence pièce justificative (défaut : `Paie_<Période>`) |
| `--par-salarie` | Écritures détaillées par salarié |
| `--rapport` | Rapport texte (défaut : `<sortie>.rapport.txt`) |

Codes de sortie : `0` OK · `1` erreur de lecture · `2` PDF non conforme · `3` anomalies détectées (fichiers générés malgré tout).

## Format du XLSX

**Feuille « Écritures »** : `Date | Compte | Libellé | Débit | Crédit | Référence | Salarié` + ligne TOTAL.

**Feuille « Récap »** : `Compte | Libellé | Total Débit | Total Crédit` + ligne TOTAL.

## Règles de précision

- Aucun montant, compte ou libellé n'est inventé : `[MISSING_DATA]` / `[NON_MAPPÉ]` si information manquante.
- Rubriques ambiguës ou inconnues : signalées dans le rapport, à compléter via `--mapping`.
- Aucune donnée personnelle sensible (ex. n° de sécurité sociale) n'est exportée.
- Montants en euros, dates `JJ/MM/AAAA`, CSV en décimales à virgule.

## Tests

```bash
python -m pytest tests/ -q
```
