import duckdb
import os

# -----------------------------------------------------------------------------
# CONFIGURATION DES CHEMINS DYNAMIQUES
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

def run_quality_engineering():
    print(f"📍 Connexion au Data Warehouse DuckDB : {DUCKDB_PATH}")
    
    if not os.path.exists(DUCKDB_PATH):
        print("❌ Erreur : Le fichier DuckDB est introuvable. Exécutez le Jour 13 d'abord.")
        return

    con = duckdb.connect(DUCKDB_PATH)

    print("==================================================")
    print("🔍 DÉBUT DU BALAYAGE QUALITY ENGINEERING & FINMA")
    print("==================================================")

    # =========================================================================
    # CONTRÔLE 1 : AUDIT DE CONFORMITÉ nLPD (ANONYMISATION IBAN)
    # =========================================================================
    nlpd_violations = con.execute("""
    SELECT COUNT(*) 
    FROM dim_clients 
    WHERE iban_anonymise NOT LIKE '____ **** **** **** *____';
    """).fetchone()[0]

    if nlpd_violations == 0:
        print("✅ Control nLPD : 100% des IBAN sont correctement anonymisés.")
    else:
        print(f"⚠️ Alerte nLPD : {nlpd_violations} violation(s) de masque IBAN détectée(s) !")

    # =========================================================================
    # CONTRÔLE 2 : DÉTECTION D'ANOMALIES FAT-FINGER (> 100,000 CHF)
    # =========================================================================
    # Seuil d'alerte métier fixé à 100'000 CHF pour contrôle manuel compliance
    SEUIL_FAT_FINGER_CHF = 100000.0

    ordres_fat_finger = con.execute(f"""
    SELECT id_ordre, id_compte, symbole, montant_brut_chf
    FROM fact_ordres_bourse
    WHERE montant_brut_chf > {SEUIL_FAT_FINGER_CHF};
    """).fetchall()

    print(f"🔎 Analyse des volumes : {len(ordres_fat_finger)} ordre(s) dépasse(nt) le seuil de {SEUIL_FAT_FINGER_CHF:,.0f} CHF.")

    # =========================================================================
    # CONTRÔLE 3 : CRÉATION DE LA TABLE DE REJETS / DEAD-LETTER QUEUE
    # =========================================================================
    con.execute(f"""
    CREATE OR REPLACE TABLE table_rejets_compliance AS
    SELECT 
        *,
        CASE 
            WHEN montant_brut_chf > {SEUIL_FAT_FINGER_CHF} THEN 'ALERT_FAT_FINGER_HIGH_VALUE'
            WHEN quantite <= 0 THEN 'ERROR_INVALID_QUANTITY'
            ELSE 'OTHER_ANOMALY'
        END AS motif_rejet,
        CURRENT_TIMESTAMP AS horodatage_controle
    FROM fact_ordres_bourse
    WHERE montant_brut_chf > {SEUIL_FAT_FINGER_CHF} OR quantite <= 0;
    """)

    nb_rejets = con.execute("SELECT COUNT(*) FROM table_rejets_compliance;").fetchone()[0]
    print(f"🛡️  Isolation Compliance : {nb_rejets} transaction(s) isolée(s) dans `table_rejets_compliance`.")

    # =========================================================================
    # CONTRÔLE 4 : EXPORTATION DU DATA LAKE CERTIFIÉ (PARQUET CLEAN)
    # =========================================================================
    # Exclusions des rejets pour le dataset de production destiné à Power BI
    con.execute(f"""
    COPY (
        SELECT f.* 
        FROM fact_ordres_bourse f
        LEFT JOIN table_rejets_compliance r ON f.id_ordre = r.id_ordre
        WHERE r.id_ordre IS NULL
    ) TO '{PARQUET_CLEAN_PATH}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');
    """)

    nb_valides = con.execute(f"SELECT COUNT(*) FROM '{PARQUET_CLEAN_PATH}'").fetchone()[0]
    print(f"✨ Data Lake Certifié : {nb_valides} ordre(s) validé(s) exporté(s) dans `{os.path.basename(PARQUET_CLEAN_PATH)}`.")

    con.close()
    print("==================================================")
    print("✅ AUDIT QUALITY ENGINEERING COMPLÉTÉ AVEC SUCCÈS")
    print("==================================================")

if __name__ == '__main__':
    run_quality_engineering()