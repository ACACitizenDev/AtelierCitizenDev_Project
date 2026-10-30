import sqlite3
import duckdb
import time
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION DES CHEMINS DYNAMIQUES
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

SQLITE_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')
DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')

def log_pipeline_step(step_name, status, message, duration_sec):
    """Enregistre le statut d'exécution dans une table de logs d'audit dans DuckDB."""
    try:
        con = duckdb.connect(DUCKDB_PATH)

        # 1. Création d'une séquence auto-incrémentée pour les ID de logs
        con.execute("CREATE SEQUENCE IF NOT EXISTS seq_pipeline_logs;")
        
        # 2. Création de la table de logs     
        con.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id_exec INTEGER DEFAULT nextval('seq_pipeline_logs'),
            etape TEXT,
            statut TEXT,
            message TEXT,
            duree_secondes REAL,
            horodatage DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # 3. Insertion du log
        con.execute("""
        INSERT INTO pipeline_execution_logs (etape, statut, message, duree_secondes)
        VALUES (?, ?, ?, ?);
        """, (step_name, status, message, round(duration_sec, 4)))
        con.close()
    except Exception as e:
        print(f"⚠️ Impossible d'écrire dans les logs DuckDB : {e}")

def run_master_pipeline():
    print("\n==================================================================")
    print("🚀 DÉMARRAGE DU MASTER PIPELINE ETL END-TO-END — BANQUE DE GENÈVE")
    print("==================================================================\n")
    
    start_total_time = time.time()

    # -------------------------------------------------------------------------
    # ÉTAPE 1 : INITIALISATION OLTP (JOUR 11)
    # -------------------------------------------------------------------------
    t0 = time.time()
    try:
        print("▶️ [1/4] Lancement Initialisation Schéma OLTP (SQLite)...")
        m01 = __import__('01_init_sqlite_oltp')
        m01.init_sqlite_oltp()
        dur = time.time() - t0
        log_pipeline_step("01_INIT_OLTP", "SUCCESS", "Schéma SQLite réinitialisé avec succès", dur)
        print(f"   ⏱️ Étape 1 complétée en {dur:.2f}s\n")
    except Exception as e:
        log_pipeline_step("01_INIT_OLTP", "FAILED", str(e), time.time() - t0)
        print(f"❌ CRITICAL ERROR Étape 1 : {e}")
        return False

    # -------------------------------------------------------------------------
    # ÉTAPE 2 : INGESTION FEEDS BNS & SMI (JOUR 12)
    # -------------------------------------------------------------------------
    t0 = time.time()
    try:
        print("▶️ [2/4] Lancement Ingestion Taux BNS & Cotations Bourse (SMI)...")
        m02 = __import__('02_ingest_feeds')
        m02.ingest_financial_feeds()
        dur = time.time() - t0
        log_pipeline_step("02_INGEST_FEEDS", "SUCCESS", "Feeds BNS et SMI ingérés avec idempotence", dur)
        print(f"   ⏱️ Étape 2 complétée en {dur:.2f}s\n")
    except Exception as e:
        log_pipeline_step("02_INGEST_FEEDS", "FAILED", str(e), time.time() - t0)
        print(f"❌ CRITICAL ERROR Étape 2 : {e}")
        return False

    # -------------------------------------------------------------------------
    # ÉTAPE 3 : TRANSFORMATION OLAP & PARQUET (JOUR 13)
    # -------------------------------------------------------------------------
    t0 = time.time()
    try:
        print("▶️ [3/4] Lancement Construction DWH DuckDB & Export Parquet Brut...")
        m03 = __import__('03_etl_duckdb_parquet')
        m03.transform_to_olap_parquet()
        dur = time.time() - t0
        log_pipeline_step("03_ETL_DUCKDB_PARQUET", "SUCCESS", "Star Schema DuckDB et Parquet générés", dur)
        print(f"   ⏱️ Étape 3 complétée en {dur:.2f}s\n")
    except Exception as e:
        log_pipeline_step("03_ETL_DUCKDB_PARQUET", "FAILED", str(e), time.time() - t0)
        print(f"❌ CRITICAL ERROR Étape 3 : {e}")
        return False

    # -------------------------------------------------------------------------
    # ÉTAPE 4 : QUALITY ENGINEERING & AUDIT FINMA (JOUR 14)
    # -------------------------------------------------------------------------
    t0 = time.time()
    try:
        print("▶️ [4/4] Lancement Audit Quality Engineering & Isolation Compliance FINMA...")
        m04 = __import__('04_quality_engineering')
        m04.run_quality_engineering()
        dur = time.time() - t0
        log_pipeline_step("04_QUALITY_ENGINEERING", "SUCCESS", "Filtres nLPD, Fat-Finger et Parquet certifié générés", dur)
        print(f"   ⏱️ Étape 4 complétée en {dur:.2f}s\n")
    except Exception as e:
        log_pipeline_step("04_QUALITY_ENGINEERING", "FAILED", str(e), time.time() - t0)
        print(f"❌ CRITICAL ERROR Étape 4 : {e}")
        return False

    total_dur = time.time() - start_total_time
    log_pipeline_step("MASTER_PIPELINE", "SUCCESS", "Pipeline exécuté avec succès de bout en bout", total_dur)
    
    print("==================================================================")
    print(f"🏆 MASTER PIPELINE EXÉCUTÉ AVEC SUCCÈS (Durée totale : {total_dur:.2f}s)")
    print("==================================================================\n")
    return True

if __name__ == '__main__':
    run_master_pipeline()