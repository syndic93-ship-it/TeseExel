TOLERANCE = 0.01


def valider(ecritures, paie=None):
    anomalies = []
    total_debit = round(sum(e.debit for e in ecritures), 2)
    total_credit = round(sum(e.credit for e in ecritures), 2)
    if abs(total_debit - total_credit) > TOLERANCE:
        anomalies.append(
            f"Déséquilibre débit/crédit : débit={total_debit:.2f} / crédit={total_credit:.2f} "
            f"(écart={round(total_debit - total_credit, 2):.2f})."
        )
    for e in ecritures:
        if e.compte.startswith("[") and e.compte.endswith("]"):
            anomalies.append(f"Compte non renseigné pour la ligne '{e.libelle}' ({e.compte}).")
    if paie is not None and paie.totaux_brut and paie.totaux_net:
        attendu = round(paie.totaux_brut - paie.totaux_cotisations, 2)
        if abs(paie.totaux_net - attendu) > TOLERANCE:
            anomalies.append(
                f"Incohérence : net à payer={paie.totaux_net:.2f} mais "
                f"brut - cotisations={attendu:.2f}."
            )
    return anomalies, total_debit, total_credit
