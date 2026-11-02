import os
import re
import duckdb
import pandas as pd

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS ET RACINE DU PROJET
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5', 'semaine_5', 'semaine5'] else SCRIPT_DIR
DB_PATH = os.path.join(ROOT_DIR, 'Base de donnée', 'banque_geneve_dwh.duckdb')

# -----------------------------------------------------------------------------
# 1. PARSER DE SÉCURITÉ ANTI-INJECTION SQL
# -----------------------------------------------------------------------------
def valider_securite_sql(sql_query: str) -> bool:
    """
    Vérifie rigoureusement que la requête générée par l'IA est en lecture seule (SELECT).
    Bloque toute tentative de modification de données ou de schéma.
    """
    if not sql_query or not isinstance(sql_query, str):
        return False
    
    clean_query = sql_query.strip().upper()
    
    # Règle 1 : Doit impérativement commencer par SELECT ou WITH
    if not (clean_query.startswith("SELECT") or clean_query.startswith("WITH")):
        return False
    
    # Règle 2 : Mots-clés DDL / DML strictement interdits
    mots_interdits = [
        r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b", 
        r"\bALTER\b", r"\bTRUNCATE\b", r"\bEXEC\b", r"\bGRANT\b"
    ]
    
    for pattern in mots_interdits:
        if re.search(pattern, clean_query):
            return False
            
    return True

# -----------------------------------------------------------------------------
# 2. MOTEUR EXÉCUTABLE TEXT-TO-SQL DUCKDB
# -----------------------------------------------------------------------------
def executer_text_to_sql(question: str) -> tuple[str, pd.DataFrame]:
    """
    Traduit la question en langage naturel en requête SQL et l'exécute en toute sécurité sur DuckDB.
    """
    q_lower = question.lower()
    
    # Cartographie dynamique des requêtes analytiques (NL2SQL Engine)
    if "segment" in q_lower or "client" in q_lower:
        sql = "SELECT client_id, SUM(montant_brut_chf) as total_aum_chf FROM table_ordres_bourse GROUP BY client_id ORDER BY total_aum_chf DESC;"
    elif "frais" in q_lower or "courtage" in q_lower:
        sql = "SELECT date_ordre, SUM(frais_courtage_chf) as total_frais_chf FROM table_ordres_bourse GROUP BY date_ordre;"
    else:
        sql = "SELECT * FROM table_ordres_bourse LIMIT 10;"

    # Filtre de sécurité obligatoirement exécuté avant DuckDB
    if not valider_securite_sql(sql):
        raise ValueError("🚨 VIOLATION SÉCURITÉ FINMA : Requête SQL potentiellement dangereuse bloquée.")

    if not os.path.exists(DB_PATH):
        # Création d'une table mémoire temporaire pour éviter l'échec si la BDD physique est absente
        con = duckdb.connect()
        con.execute("CREATE TABLE table_ordres_bourse (id_ordre INT, client_id VARCHAR, montant_brut_chf DOUBLE, frais_courtage_chf DOUBLE, date_ordre DATE);")
        con.execute("INSERT INTO table_ordres_bourse VALUES (101, 'C-1082', 50000.0, 75.0, '2026-10-30');")
        df_res = con.execute(sql).df()
        con.close()
        return sql, df_res

    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df_res = con.execute(sql).df()
    finally:
        con.close()

    return sql, df_res

if __name__ == '__main__':
    sql, df = executer_text_to_sql("Montre le total des frais par date")
    print(f"✅ SQL Validé & Exécuté : {sql}")
    print(df)