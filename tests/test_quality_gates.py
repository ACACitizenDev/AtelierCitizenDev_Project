import os
import pytest
import duckdb

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS D'ACCÈS
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'tests' else SCRIPT_DIR
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

# -----------------------------------------------------------------------------
# SUITE DE TESTS UNITAIRES RIGOUREUSE & DÉFENSIVE
# -----------------------------------------------------------------------------

def test_parquet_existence():
    """T1 : Vérifie que le Data Lake Parquet certifié existe sur le disque."""
    assert os.path.exists(PARQUET_CLEAN_PATH), f"❌ Fichier Parquet introuvable dans : {PARQUET_CLEAN_PATH}"


def test_no_fat_finger_in_clean_parquet():
    """T2 : Contrôle FINMA - Aucun ordre > 100k CHF dans le Parquet Clean."""
    if not os.path.exists(PARQUET_CLEAN_PATH):
        pytest.skip("Fichier Parquet absent - Test ignoré.")

    con = duckdb.connect()
    res = con.execute(f"SELECT MAX(montant_brut_chf) FROM '{PARQUET_CLEAN_PATH}'").fetchone()
    con.close()

    # Gestion défensive du None si la table ou le Parquet est vide
    max_amount = res[0] if (res and res[0] is not None) else 0.0
    assert max_amount <= 100000.0, f"🚨 VIOLATION FINMA : Ordre de {max_amount:,.2f} CHF détecté !"


def test_brokerage_fee_calculation():
    """T3 : Vérifie la formule des frais de courtage (0.15%)."""
    if not os.path.exists(PARQUET_CLEAN_PATH):
        pytest.skip("Fichier Parquet absent - Test ignoré.")

    con = duckdb.connect()
    row = con.execute(f"SELECT montant_brut_chf, frais_courtage_chf FROM '{PARQUET_CLEAN_PATH}' WHERE montant_brut_chf > 0 LIMIT 1").fetchone()
    con.close()

    # Vérification que la ligne existe ET contient des valeurs non-nulles
    if row and row[0] is not None and row[1] is not None:
        montant_brut, frais_preleves = row[0], row[1]
        frais_attendus = round(montant_brut * 0.0015, 4)
        assert abs(frais_preleves - frais_attendus) < 0.05, f"❌ Incohérence frais : Prélevé={frais_preleves}, Attendu={frais_attendus}"
    else:
        pytest.skip("Aucune donnée disponible dans le fichier Parquet pour calculer les frais.")


def test_duckdb_tables_schema():
    """T4 : Vérifie la présence des tables obligatoires dans DuckDB."""
    if not os.path.exists(DUCKDB_PATH):
        pytest.skip("Base DuckDB absente - Test ignoré.")

    con = duckdb.connect(DUCKDB_PATH)
    tables_result = con.execute("SHOW TABLES;").fetchall()
    con.close()

    tables = [t[0] for t in tables_result] if tables_result else []
    tables_attendues = ['fact_ordres_bourse', 'dim_clients', 'dim_titres', 'table_rejets_compliance']
    
    for table in tables_attendues:
        assert table in tables, f"❌ Table obligatoire manquante dans DuckDB : {table}"


def test_table_rejets_compliance_queryable():
    """T5 : Vérifie que table_rejets_compliance est interrogeable même si elle est vide (0 ligne)."""
    if not os.path.exists(DUCKDB_PATH):
        pytest.skip("Base DuckDB absente - Test ignoré.")

    con = duckdb.connect(DUCKDB_PATH)
    try:
        count = con.execute("SELECT COUNT(*) FROM table_rejets_compliance;").fetchone()[0]
        # Valide si le nombre de rejets est supérieur ou égal à 0
        assert count >= 0, "Le nombre de rejets doit être >= 0"
    finally:
        con.close()