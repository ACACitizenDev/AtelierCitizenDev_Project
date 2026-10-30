import sqlite3

def run_integrity_tests():
    conn = sqlite3.connect('banque_geneve_oltp.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print("--- 🧪 DÉBUT DES TESTS D'INTÉGRITÉ SQLITE ---")

    # TEST A : Insertion d'un ordre valide
    try:
        cursor.execute("""
        INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution)
        VALUES ('ORD-2026-001', 'CPT-1001', 'BCGE.SW', 'Achat', 50, 220.00);
        """)
        conn.commit()
        print("✅ Test A Réussi : Ordre valide inséré.")
    except Exception as e:
        print(f"❌ Test A Échoué : {e}")

    # TEST B : Vérification du calcul automatique des colonnes générées
    cursor.execute("SELECT montant_brut_chf, frais_courtage_chf FROM ordres_bourse WHERE id_ordre = 'ORD-2026-001';")
    montant, frais = cursor.fetchone()
    print(f"👉 Calcul Automatique : Montant Brut = {montant:.2f} CHF | Frais (0.15%) = {frais:.2f} CHF")

    # TEST C : Tentative d'insertion d'une quantité négative (Doit échouer)
    try:
        cursor.execute("""
        INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution)
        VALUES ('ORD-2026-002', 'CPT-1001', 'BCGE.SW', 'Achat', -10, 220.00);
        """)
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"✅ Test C Réussi (Rejet attendu) : Contrainte CHECK quantité > 0 déclenchée.")

    # TEST D : Tentative d'insertion d'un compte inexistant (FK Violation)
    try:
        cursor.execute("""
        INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution)
        VALUES ('ORD-2026-003', 'CPT-9999', 'BCGE.SW', 'Achat', 10, 220.00);
        """)
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"✅ Test D Réussi (Rejet attendu) : Clé étrangère id_compte bloquée.")

    conn.close()

if __name__ == '__main__':
    run_integrity_tests()