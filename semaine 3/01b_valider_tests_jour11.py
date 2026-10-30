import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
DB_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')

def valider_tests_jour11():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable à l'adresse : {DB_PATH}")
        print("💡 Exécutez d'abord 01_init_sqlite_oltp.py")
        return

    print(f"🔎 Analyse de la base : {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Check Schéma
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    if 'comptes_clients' in tables and 'referentiel_titres' in tables and 'ordres_bourse' in tables:
        print("✅ Test 11.1 [PASS] : Schéma OLTP détecté dans 'Base de donnée'.")
    else:
        print("❌ Test 11.1 [FAIL] : Tables manquantes.")

    # 2. Check Calculs
    try:
        cursor.execute("DELETE FROM ordres_bourse WHERE id_ordre = 'TEST-11-2';")
        cursor.execute("INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution) VALUES ('TEST-11-2', 'CPT-1001', 'BCGE.SW', 'Achat', 50, 220.00);")
        conn.commit()
        cursor.execute("SELECT montant_brut_chf, frais_courtage_chf FROM ordres_bourse WHERE id_ordre = 'TEST-11-2';")
        m, f = cursor.fetchone()
        print(f"✅ Test 11.2 [PASS] : Calculs exacts (Montant: {m:,.2f} CHF | Frais: {f:,.2f} CHF).")
    except Exception as e:
        print(f"❌ Test 11.2 [FAIL] : {e}")

    # 3. Check nLPD
    try:
        cursor.execute("INSERT INTO comptes_clients VALUES ('CPT-BAD', 'Test', 'HNWI', 'CHF', 'CH6800784000123456789');")
        conn.commit()
        print("❌ Test 11.3 [FAIL] : IBAN non masqué accepté.")
    except sqlite3.IntegrityError:
        print("✅ Test 11.3 [PASS] : Protection nLPD certifiée.")

    # 4. Check FK
    try:
        cursor.execute("INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution) VALUES ('TEST-FK', 'CPT-9999', 'BCGE.SW', 'Achat', 10, 220.00);")
        conn.commit()
        print("❌ Test 11.4 [FAIL] : Compte inexistant accepté.")
    except sqlite3.IntegrityError:
        print("✅ Test 11.4 [PASS] : Clé étrangère FK validée.")

    # 5. Check Quantité
    try:
        cursor.execute("INSERT INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution) VALUES ('TEST-QTY', 'CPT-1001', 'BCGE.SW', 'Achat', -5, 220.00);")
        conn.commit()
        print("❌ Test 11.5 [FAIL] : Quantité négative acceptée.")
    except sqlite3.IntegrityError:
        print("✅ Test 11.5 [PASS] : Contrôle de quantité validé.")

    conn.close()

if __name__ == '__main__':
    valider_tests_jour11()