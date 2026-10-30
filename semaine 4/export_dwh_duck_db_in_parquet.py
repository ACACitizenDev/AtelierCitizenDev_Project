import duckdb
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')

# Connexion à DuckDB
con = duckdb.connect(DUCKDB_PATH)

# Exportation des tables de dimensions au format Parquet
con.execute(f"COPY dim_clients TO '{os.path.join(DB_DIR, 'dim_clients.parquet')}' (FORMAT PARQUET);")
con.execute(f"COPY dim_titres TO '{os.path.join(DB_DIR, 'dim_titres.parquet')}' (FORMAT PARQUET);")

con.close()
print("✅ Fichiers dim_clients.parquet et dim_titres.parquet générés avec succès !")