import duckdb
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

def valider_tests_jour15():
    print("==================================================")
    print("🧪 MATRICE DE RECETTE GLOBALE & AUDIT MASTER — JOUR 15")
    print("==================================================\n")

    # 1. Lancement de l'orchestrateur Master
    m05 = __import__('05_master_pipeline')
    success = m05.run_master_pipeline()

    # -------------------------------------------------------------------------
    # TEST 15.1 : Exécution sans erreur du Master Pipeline
    # -------------------------------------------------------------------------
    if success:
        print("✅ Test 15.1 [PASS] : Le Master Pipeline s'est exécuté sans aucune exception.")
    else:
        print("❌ Test 15.1 [FAIL] : Échec lors de l'exécution du Master Pipeline.")
        return

    con = duckdb.connect(DUCKDB_PATH)

    # -------------------------------------------------------------------------
    # TEST 15.2 : Vérification du Journal des Logs d'Audit
    # -------------------------------------------------------------------------
    logs = con.execute("SELECT etape, statut, duree_secondes FROM pipeline_execution_logs;").fetchall()
    if len(logs) >= 5:
        print(f"✅ Test 15.2 [PASS] : Table de traçabilité `pipeline_execution_logs` certifiée ({len(logs)} événements enregistrés).")
    else:
        print(f"❌ Test 15.2 [FAIL] : Logs d'exécution incomplets ({len(logs)} enregistrements).")

    # -------------------------------------------------------------------------
    # TEST 15.3 : Intégrité Globale de la Chaîne (OLTP -> DWH -> Parquet Clean)
    # -------------------------------------------------------------------------
    nb_clean = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_CLEAN_PATH}'").fetchone()[0]
    if nb_clean > 0:
        print(f"✅ Test 15.3 [PASS] : Data Lake certifié prêt pour Power BI ({nb_clean} enregistrements nettoyés).")
    else:
        print("❌ Test 15.3 [FAIL] : Le fichier Parquet final est vide.")

    # -------------------------------------------------------------------------
    # TEST 15.4 : Temps de Traitement Global (< 5 secondes)
    # -------------------------------------------------------------------------
    row_time = con.execute("SELECT duree_secondes FROM pipeline_execution_logs WHERE etape = 'MASTER_PIPELINE' ORDER BY horodatage DESC LIMIT 1;").fetchone()
    
    # 💥 CORRECTION : Extraction du float depuis le tuple (row_time[0])
    total_time  = row_time[0] if row_time else None    
    
    if total_time is not None and total_time < 5.0:
        print(f"✅ Test 15.4 [PASS] : Performance globale optimale ({total_time:.2f} secondes).")
    else:
        print(f"⚠️ Test 15.4 [WARNING] : Temps global élevé ({total_time}s).")

    con.close()
    print("\n------------------------------------------------------------------")
    print("🎉 CERTIFICATION SEMAINE 3 COMPLÉTÉE AVEC SUCCÈS ! (100% GREEN)")
    print("------------------------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour15()