import duckdb
import os
import time
from datetime import datetime

# -----------------------------------------------------------------------------
# CHEMINS DES FICHIERS
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')
PARQUET_CLIENTS_PATH = os.path.join(DB_DIR, 'dim_clients.parquet')
PARQUET_TITRES_PATH = os.path.join(DB_DIR, 'dim_titres.parquet')

def run_production_refresh():
    print("==================================================================")
    print("🔄 DÉMARRAGE DU RAFRAÎCHISSEMENT GLOBAL DE PRODUCTION — POWER BI")
    print("==================================================================\n")
    
    t0 = time.time()
    
    # 1. Lancement du Master Pipeline ETL (Semaine 3)
    try:

        sys_path_added = False
        import sys
        semaine3_dir = os.path.join(PARENT_DIR, 'semaine 3')
        if semaine3_dir not in sys.path:
            sys.path.append(semaine3_dir)
            sys_path_added = True

        m05 = __import__('05_master_pipeline')
        success = m05.run_master_pipeline()
        
        if not success:
            raise RuntimeError("Le Master Pipeline ETL a échoué.")
            
    except Exception as e:
        print(f"❌ ÉCHEC CRITIQUE lors de l'exécution du Master Pipeline : {e}")
        return False

    # 2. Exportation / Actualisation des dimensions Parquet pour Power BI
    try:
        print("▶️ Actualisation des fichiers Parquet de Dimensions...")
        con = duckdb.connect(DUCKDB_PATH)
        con.execute(f"COPY dim_clients TO '{PARQUET_CLIENTS_PATH}' (FORMAT PARQUET);")
        con.execute(f"COPY dim_titres TO '{PARQUET_TITRES_PATH}' (FORMAT PARQUET);")
        
        # Vérification des volumes
        nb_ordres = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_CLEAN_PATH}'").fetchone()
        nb_clients = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_CLIENTS_PATH}'").fetchone()
        nb_titres = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_TITRES_PATH}'").fetchone()
        con.close()
        
        dur = time.time() - t0
        print(f"   ✓ fact_ordres_bourse : {nb_ordres} lignes")
        print(f"   ✓ dim_clients : {nb_clients} lignes")
        print(f"   ✓ dim_titres : {nb_titres} lignes")
        print(f"⏱️ Rafraîchissement Data Lake achevé en {dur:.2f} secondes.\n")
        return True
        
    except Exception as e:
        print(f"❌ ÉCHEC lors de l'actualisation des Parquet Dimensions : {e}")
        return False

if __name__ == '__main__':
    run_production_refresh()