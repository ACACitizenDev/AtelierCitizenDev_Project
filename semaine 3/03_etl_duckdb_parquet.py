import sqlite3
import duckdb
import pandas as pd
import os

# -----------------------------------------------------------------------------
# CONFIGURATION DES CHEMINS DYNAMIQUES
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)

SQLITE_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')
DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_PATH = os.path.join(DB_DIR, 'ordres_bourse_2026.parquet')

def transform_to_olap_parquet():
    print(f"📍 Connexion à la source OLTP SQLite : {SQLITE_PATH}")
    
    if not os.path.exists(SQLITE_PATH):
        print("❌ Erreur : La base SQLite n'existe pas. Exécutez d'abord Jour 11 et Jour 12.")
        return

    # =========================================================================
    # ÉTAPE 1 : EXTRACTION DE LA BASE OLTP (SQLITE -> PANDAS)
    # =========================================================================
    conn_sqlite = sqlite3.connect(SQLITE_PATH)
    
    df_clients = pd.read_sql_query("SELECT * FROM comptes_clients", conn_sqlite)
    df_titres = pd.read_sql_query("SELECT * FROM referentiel_titres", conn_sqlite)
    df_ordres = pd.read_sql_query("SELECT * FROM ordres_bourse", conn_sqlite)
    
    ## Ajout / Réinitialisation explicite des colonnes calculées dans Pandas
    #df_ordres['montant_brut_chf'] = df_ordres['quantite'] * df_ordres['prix_execution']
    #df_ordres['frais_courtage_chf'] = df_ordres['montant_brut_chf'] * 0.0015

    conn_sqlite.close()
    print(f"📦 Données extraites depuis SQLite : {len(df_ordres)} ordres, {len(df_clients)} clients, {len(df_titres)} titres.")

    # =========================================================================
    # ÉTAPE 2 : CHARGEMENT ET MODÉLISATION EN ÉTOILE DANS DUCKDB
    # =========================================================================
    print(f"📍 Alimentation du Data Warehouse DuckDB : {DUCKDB_PATH}")
    con_duck = duckdb.connect(DUCKDB_PATH)

    # Ingestion directe des DataFrames Pandas dans DuckDB (Zero-Copy)
    con_duck.execute("CREATE OR REPLACE TABLE dim_clients AS SELECT * FROM df_clients;")
    con_duck.execute("CREATE OR REPLACE TABLE dim_titres AS SELECT * FROM df_titres;")
    con_duck.execute("CREATE OR REPLACE TABLE fact_ordres_bourse AS SELECT * FROM df_ordres;")

    print("✅ Modèle en Étoile OLAP (Star Schema) créé dans DuckDB.")

    # =========================================================================
    # ÉTAPE 3 : EXPORTATION AU FORMAT PARQUET COMPRESSÉ (SNAPPY)
    # =========================================================================
    con_duck.execute(f"""
    COPY fact_ordres_bourse TO '{PARQUET_PATH}' 
    (FORMAT PARQUET, COMPRESSION 'SNAPPY');
    """)
    print(f"✅ Export Parquet Snappy généré : {PARQUET_PATH}")

    # =========================================================================
    # ÉTAPE 4 : VERIFICATION & REQUÊTE DUCKDB DIRECTE SUR LE PARQUET
    # =========================================================================
    df_parquet_check = con_duck.execute(f"SELECT * FROM '{PARQUET_PATH}'").df()
    
    con_duck.close()
    print(f"✅ Validation Parquet : {len(df_parquet_check)} lignes relues avec succès directement depuis le fichier Parquet !")

if __name__ == '__main__':
    transform_to_olap_parquet()