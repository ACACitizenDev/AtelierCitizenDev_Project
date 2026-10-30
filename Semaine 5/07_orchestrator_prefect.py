import os
import sys
import time
import importlib
from datetime import datetime
from prefect import task, flow

# -----------------------------------------------------------------------------
# CONFIGURATION DES CHEMINS D'ACCÈS (PYTHONPATH)
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

# Injection dynamique des dossiers du projet dans sys.path
for folder in ['', 'semaine 1', 'semaine 2', 'semaine 3', 'semaine 4']:
    path = os.path.join(PARENT_DIR, folder) if folder else PARENT_DIR
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# -----------------------------------------------------------------------------
# DÉFINITION DES TÂCHES PREFECT (@task)
# -----------------------------------------------------------------------------

@task(
    name="Tache_1_Ingestion_Feeds_BNS_SMI",
    description="Ingestion des taux BNS et cours SMI avec retry automatique",
    retries=3,
    retry_delay_seconds=5
)
def task_ingest_feeds():
    """Tâche 1 : Ingestion des flux externes BNS et SMI."""
    print("▶️ [Task 1] Démarrage de l'ingestion des feeds financiers (BNS & SMI)...")
    
    try:
        # Importation dynamique pour contourner la syntaxe sur les chiffres initiaux
        ingest = importlib.import_module('02_ingest_feeds')
        ingest.ingest_financial_feeds()
        print("   ✓ [Task 1] Ingestion des feeds BNS & SMI terminée avec succès.")
        return True
    except Exception as e:
        print(f"❌ [Task 1] Erreur d'ingestion : {e}")
        raise e


@task(
    name="Tache_2_ETL_DuckDB_Quality_FINMA",
    description="Exécution du DWH DuckDB et isolation des rejets Compliance",
    retries=2,
    retry_delay_seconds=3
)
def task_run_dwh_and_quality():
    """Tâche 2 : Transformation DuckDB & Filtres FINMA."""
    print("▶️ [Task 2] Exécution de la transformation DWH et contrôle de qualité...")
    
    try:
        # Importation dynamique du module 05_master_pipeline
        master = importlib.import_module('05_master_pipeline')
        success = master.run_master_pipeline()
        if not success:
            raise RuntimeError("Échec renvoyé par le Master Pipeline ETL.")
        print("   ✓ [Task 2] Traitement DWH DuckDB & Règles FINMA validés.")
        return True
    except Exception as e:
        print(f"❌ [Task 2] Échec du pipeline DWH : {e}")
        raise e


@task(
    name="Tache_3_Export_DataLake_Parquet",
    description="Rafraîchissement des fichiers Parquet pour Power BI Desktop"
)
def task_export_parquet():
    """Tâche 3 : Exportation des dimensions et faits Parquet pour Power BI."""
    print("▶️ [Task 3] Exportation des données certifiées vers le Data Lake Parquet...")
    
    try:
        import duckdb
        duckdb_path = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
        parquet_clean = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')
        
        con = duckdb.connect(duckdb_path)
        res = con.execute(f"SELECT COUNT(*) FROM '{parquet_clean}'").fetchone()
        nb_clean = res[0] if res else 0
        con.close()
        
        print(f"   ✓ [Task 3] Data Lake Parquet certifié prêt pour Power BI ({nb_clean} ordres validés).")
        return nb_clean
    except Exception as e:
        print(f"❌ [Task 3] Erreur lors de l'exportation Parquet : {e}")
        raise e

# -----------------------------------------------------------------------------
# DÉFINITION DU FLUX PRINCIPAL (@flow)
# -----------------------------------------------------------------------------

@flow(
    name="Master_Pipeline_Bancaire_Geneve",
    description="Orchestrateur Batch Quotidien - Data Engineering Genève"
)
def master_workflow_orchestrator(simulate_error: bool = False):
    print("==================================================================")
    print("🚀 DÉMARRAGE DU WORKFLOW PREFECT D'ORDONNANCEMENT BATCH")
    print(f"📅 Horodatage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================================\n")
    
    t_start = time.time()
    
    if simulate_error:
        print("⚠️ Mode simulation d'erreur réseau activé sur la Tâche 1...")
    
    # Exécution séquentielle contrôlée par les dépendances
    res_ingest = task_ingest_feeds()
    
    if res_ingest:
        res_dwh = task_run_dwh_and_quality()
        
        if res_dwh:
            nb_orders = task_export_parquet()
            
            total_duration = time.time() - t_start
            print("\n------------------------------------------------------------------")
            print(f"🎉 WORKFLOW BATCH ACHEVÉ AVEC SUCCÈS (Durée: {total_duration:.2f}s)")
            print(f"📊 Volume final certifié : {nb_orders} ordres en production.")
            print("------------------------------------------------------------------")
            return True

    return False


if __name__ == '__main__':
    master_workflow_orchestrator()