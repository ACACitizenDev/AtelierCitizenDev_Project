import os
import sys
import pandas as pd
import duckdb
from datetime import datetime
from prefect import task, flow

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS ET RACINE DU PROJET
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5v2', 'semaine_5v2', 'semaine5v2'] else SCRIPT_DIR
DB_DIR = os.path.join(ROOT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

# -----------------------------------------------------------------------------
# TÂCHES PREFECT AVEC STRATÉGIE DE RETRY AUTOMATIQUE
# -----------------------------------------------------------------------------

@task(name="Ingestion_Taux_et_Ordres", retries=3, retry_delay_seconds=5)
def task_ingestion_flux_bancaire() -> pd.DataFrame:
    """
    Simule la collecte du flux d'ordres de bourse du jour.
    En cas d'échec réseau simulé, Prefect réessaie jusqu'à 3 fois.
    """
    print("▶️ [Task 1] Extraction du flux d'ordres bancaires...")
    
    data = [
        {"id_ordre": 2001, "client_id": "C-1082", "isin": "CH0012056047", "quantite": 300, "prix_unitaire_chf": 28.50, "date_ordre": "2026-10-30"},
        {"id_ordre": 2002, "client_id": "C-4421", "isin": "CH0038863350", "quantite": 150, "prix_unitaire_chf": 112.00, "date_ordre": "2026-10-30"},
        {"id_ordre": 2003, "client_id": "C-9901", "isin": "CH0012005267", "quantite": 500, "prix_unitaire_chf": 94.50, "date_ordre": "2026-10-30"}
    ]
    df = pd.DataFrame(data)
    df['montant_brut_chf'] = round(df['quantite'] * df['prix_unitaire_chf'], 2)
    df['frais_courtage_chf'] = round(df['montant_brut_chf'] * 0.0015, 4)
    return df


@task(name="Persistance_DWH_DuckDB", retries=2, retry_delay_seconds=3)
def task_persistance_duckdb(df: pd.DataFrame):
    """
    Persiste les transactions certifiées dans le Data Warehouse DuckDB et en Parquet.
    """
    print("▶️ [Task 2] Sauvegarde dans DuckDB et export Parquet...")
    
    # Export Parquet
    df.to_parquet(PARQUET_PATH, index=False)
    
    # Alimentation DuckDB
    con = duckdb.connect(DUCKDB_PATH)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS table_ordres_bourse AS SELECT * FROM df WHERE 1=0;")
        con.execute("INSERT INTO table_ordres_bourse SELECT * FROM df;")
    finally:
        con.close()
    print(f"✅ Data Lake & DWH alimentés avec succès ({len(df)} lignes).")


@flow(name="Pipeline_Ordonnance_Jour21")
def pipeline_jour21_master():
    """
    Flow Master d'ordonnancement pour la Journée 21.
    """
    df_ordres = task_ingestion_flux_bancaire()
    task_persistance_duckdb(df_ordres)

if __name__ == '__main__':
    pipeline_jour21_master()