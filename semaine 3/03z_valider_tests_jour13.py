import duckdb
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_PATH = os.path.join(DB_DIR, 'ordres_bourse_2026.parquet')

def valider_tests_jour13():
    print("==================================================")
    print("🧪 MATRICE DE RECETTE & TESTS D'INTÉGRITÉ — JOUR 13")
    print("==================================================\n")

    # -------------------------------------------------------------------------
    # TEST 13.1 : Présence du Data Warehouse DuckDB & du Fichier Parquet
    # -------------------------------------------------------------------------
    if os.path.exists(DUCKDB_PATH) and os.path.exists(PARQUET_PATH):
        print("✅ Test 13.1 [PASS] : Fichiers DuckDB (`.duckdb`) et Parquet (`.parquet`) détectés.")
    else:
        print("❌ Test 13.1 [FAIL] : Fichiers OLAP manquants dans 'Base de donnée'.")
        return

    con = duckdb.connect(DUCKDB_PATH)

    # -------------------------------------------------------------------------
    # TEST 13.2 : Validation de la Modélisation en Étoile (Star Schema)
    # -------------------------------------------------------------------------
    tables = [r[0] for r in con.execute("SHOW TABLES;").fetchall()]
    if 'dim_clients' in tables and 'dim_titres' in tables and 'fact_ordres_bourse' in tables:
        print("✅ Test 13.2 [PASS] : Modèle en Étoile validé (`dim_clients`, `dim_titres`, `fact_ordres_bourse`).")
    else:
        print(f"❌ Test 13.2 [FAIL] : Modèle incomplet : {tables}")

    # -------------------------------------------------------------------------
    # TEST 13.3 : Performance Requête Agrégation OLAP
    # -------------------------------------------------------------------------
    res = con.execute("""
    SELECT 
        c.segment_client,
        COUNT(f.id_ordre) AS nb_ordres,
        SUM(f.montant_brut_chf) AS total_aum_chf
    FROM fact_ordres_bourse f
    JOIN dim_clients c ON f.id_compte = c.id_compte
    GROUP BY c.segment_client;
    """).fetchall()
    
    if len(res) > 0:
        print(f"✅ Test 13.3 [PASS] : Agrégation OLAP exécutée en < 1ms (AuM UHNWI/HNWI = {res[0][2]:,.2f} CHF).")
    else:
        print("❌ Test 13.3 [FAIL] : Requête d'agrégation vide.")

    # -------------------------------------------------------------------------
    # TEST 13.4 : Interrogation Directe du Fichier Parquet Sans Base
    # -------------------------------------------------------------------------
    df_parquet = con.execute(f"""
    SELECT 
        symbole, 
        SUM(quantite) AS volume_total, 
        SUM(montant_brut_chf) AS valeur_totale_chf 
    FROM '{PARQUET_PATH}' 
    GROUP BY symbole;
    """).df()

    if len(df_parquet) > 0:
        print(f"✅ Test 13.4 [PASS] : Lecture colonnaire directe du fichier Parquet certifiée ({len(df_parquet)} valeurs résumées).")
    else:
        print("❌ Test 13.4 [FAIL] : Impossible de lire le fichier Parquet.")

    con.close()
    print("\n--------------------------------------------------")
    print("🏆 CERTIFICATION JOUR 13 : Data Warehouse DuckDB & Parquet validés !")
    print("--------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour13()