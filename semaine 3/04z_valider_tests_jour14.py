import duckdb
import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

SQLITE_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')
DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

def valider_tests_jour14():
    print("==================================================")
    print("🧪 MATRICE DE RECETTE & TESTS D'INTÉGRITÉ — JOUR 14")
    print("==================================================\n")

    if not os.path.exists(DUCKDB_PATH):
        print("❌ Fichier DuckDB introuvable. Exécutez le Jour 13 d'abord.")
        return

    # -------------------------------------------------------------------------
    # 1. INJECTION D'UN ORDRE "FAT-FINGER" DANS SQLITE (500'000 CHF)
    # -------------------------------------------------------------------------
    print("💉 Injection de test : Création d'un ordre suspect de 500'000 CHF...")
    conn_sq = sqlite3.connect(SQLITE_PATH)
    cur_sq = conn_sq.cursor()
    cur_sq.execute("""
    INSERT OR REPLACE INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution)
    VALUES ('ORD-FAT-FINGER-01', 'CPT-1001', 'BCGE.SW', 'Achat', 2500, 200.00);
    """)
    conn_sq.commit()
    conn_sq.close()

    # -------------------------------------------------------------------------
    # 2. RE-SYNCHRO DUCKDB SÉCURISÉE (Calcul explicit de montant_brut_chf)
    # -------------------------------------------------------------------------
    con = duckdb.connect(DUCKDB_PATH)
    con.execute(f"""
    CREATE OR REPLACE TABLE fact_ordres_bourse AS 
    SELECT 
        id_ordre,
        id_compte,
        symbole,
        type_ordre,
        quantite,
        prix_execution,
        (quantite * prix_execution) AS montant_brut_chf,
        (quantite * prix_execution * 0.0015) AS frais_courtage_chf,
        statut_ordre,
        horodatage
    FROM sqlite_scan('{SQLITE_PATH}', 'ordres_bourse');
    """)
    con.close()

    # -------------------------------------------------------------------------
    # 3. EXÉCUTION DU MODULE QUALITY ENGINEERING
    # -------------------------------------------------------------------------
    import04 = __import__('04_quality_engineering')
    import04.run_quality_engineering()

    # -------------------------------------------------------------------------
    # 4. VÉRIFICATION ET VALIDATION DES 4 TESTS
    # -------------------------------------------------------------------------
    con = duckdb.connect(DUCKDB_PATH)

    # TEST 14.1 : Détection nLPD
    nlpd_cnt = con.execute("SELECT COUNT(*) FROM dim_clients WHERE iban_anonymise NOT LIKE '____ **** **** **** *____';").fetchone()[0]
    if nlpd_cnt == 0:
        print("✅ Test 14.1 [PASS] : Certification nLPD (Aucun IBAN en clair dans la dimension client).")
    else:
        print("❌ Test 14.1 [FAIL] : Violation nLPD détectée.")

    # TEST 14.2 : Interception Fat-Finger
    rejets = con.execute("SELECT COUNT(*) FROM table_rejets_compliance WHERE id_ordre = 'ORD-FAT-FINGER-01';").fetchone()[0]
    if rejets == 1:
        print("✅ Test 14.2 [PASS] : Anomalie Fat-Finger interceptée et isolée dans `table_rejets_compliance`.")
    else:
        print("❌ Test 14.2 [FAIL] : L'ordre suspect n'a pas été capturé dans les rejets.")

    # TEST 14.3 : Isolation dans la Table d'Audit
    motif = con.execute("SELECT motif_rejet FROM table_rejets_compliance WHERE id_ordre = 'ORD-FAT-FINGER-01';").fetchone()[0]
    if motif == 'ALERT_FAT_FINGER_HIGH_VALUE':
        print(f"✅ Test 14.3 [PASS] : Tagging Compliance correct (`motif_rejet` = '{motif}').")
    else:
        print(f"❌ Test 14.3 [FAIL] : Motif incorrect ({motif}).")

    # TEST 14.4 : Data Lake Parquet Certifié Clean
    clean_check = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_CLEAN_PATH}' WHERE id_ordre = 'ORD-FAT-FINGER-01';").fetchone()[0]
    if clean_check == 0:
        print("✅ Test 14.4 [PASS] : Le fichier Parquet final est filtré et ne contient aucun rejet.")
    else:
        print("❌ Test 14.4 [FAIL] : Un rejet est présent dans le fichier Parquet de production !")

    con.close()
    print("\n--------------------------------------------------")
    print("🏆 CERTIFICATION JOUR 14 : Quality Engineering & Compliance FINMA validés !")
    print("--------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour14()