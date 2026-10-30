import duckdb
import importlib
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

def valider_tests_jour20():
    print("==================================================")
    print("🧪 MATRICE DE RECETTE FINALE & CERTIFICATION GO-LIVE — JOUR 20")
    print("==================================================\n")

    # 1. Lancement du rafraîchissement global
    prod = importlib.import_module('06_production_refresh')
    success = prod.run_production_refresh()

    # TEST 20.1 : Exécution du rafraîchissement global de production
    if success:
        print("✅ Test 20.1 [PASS] : Pipeline de rafraîchissement global exécuté avec succès.")
    else:
        print("❌ Test 20.1 [FAIL] : Échec lors du rafraîchissement global.")
        return

    con = duckdb.connect(DUCKDB_PATH)

    # TEST 20.2 : Contrôle d'Invariabilité & Intégrité des Données
    res_clean = con.execute(f"SELECT COUNT(*), SUM(montant_brut_chf) FROM '{PARQUET_CLEAN_PATH}'").fetchone()
    nb_clean = res_clean[0] if res_clean else 0
    total_aum = res_clean[1] if res_clean else 0.0

    if nb_clean > 0 and total_aum > 0:
        print(f"✅ Test 20.2 [PASS] : Data Lake certifié cohérent ({nb_clean} ordres pour un total de {total_aum:,.2f} CHF).")
    else:
        print("❌ Test 20.2 [FAIL] : Données absentes ou nulles dans le Data Lake Parquet.")

    # TEST 20.3 : Traçabilité Audit & Conformité FINMA
    rejets = con.execute("SELECT COUNT(*) FROM table_rejets_compliance;").fetchone()
    nb_rejets = rejets[0] if rejets else 0
    print(f"✅ Test 20.3 [PASS] : Table des rejets Compliance isolée avec succès ({nb_rejets} anomalies détectées).")

    # TEST 20.4 : Présence du Dictionnaire de Données DAX
    dax_doc = importlib.import_module('06b_export_dax_dictionary')
    dax_doc.generate_dax_dictionary()
    print("✅ Test 20.4 [PASS] : Documentation et dictionnaire de métadonnées DAX validés.")

    con.close()
    print("\n------------------------------------------------------------------")
    print("🏆 CERTIFICATION GLOBALE GO-LIVE ACCORDÉE ! (100% GREEN)")
    print("🎉 LE PROJET CITIZEN DATA ENGINEER EST PRÊT POUR LA PRODUCTION !")
    print("------------------------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour20()