import os
import sys
import importlib
import pandas as pd
import duckdb
from datetime import datetime
from prefect import task, flow

# -----------------------------------------------------------------------------
# 1. RÉSOLUTIONS ET CONFIGURATION DES CHEMINS D'ACCÈS
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Détermination de la racine du projet (dossier parent si exécuté depuis 'semaine 5')
if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5', 'semaine_5', 'semaine5']:
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
else:
    ROOT_DIR = SCRIPT_DIR

DB_DIR = os.path.join(ROOT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

# Ajout du sous-dossier au sys.path pour l'import dynamique
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# -----------------------------------------------------------------------------
# 2. IMPORTS DYNAMIQUES DES MODULES DE LOGGING ET D'ALERTING (JOUR 24)
# -----------------------------------------------------------------------------
try:
    logger_module = importlib.import_module("07e_logger_config")
    logger = logger_module.logger
except Exception as e:
    import logging
    logger = logging.getLogger("BanqueGeneveLogger")
    logging.basicConfig(level=logging.INFO)
    logger.warning(f"⚠️ Chargement du logger par défaut (erreur d'import : {e})")

try:
    alert_module = importlib.import_module("07_alert_notifier")
    envoyer_alerte_compliance = alert_module.envoyer_alerte_compliance
except Exception as e:
    def envoyer_alerte_compliance(id_ordre, client_id, montant_chf, motif="Fat-Finger (> 100k CHF)", webhook_url=None):
        logger.error(f"🚨 [ALERTE FALLBACK] Ordre #{id_ordre} | Client {client_id} | Montant {montant_chf:,.2f} CHF | Motif: {motif}")
        return True

# -----------------------------------------------------------------------------
# 3. TÂCHES PREFECT (TASKS)
# -----------------------------------------------------------------------------

@task(name="Tache_1_Ingestion_Ordres_Bourse", retries=2, retry_delay_seconds=5)
def task_ingestion_ordres() -> pd.DataFrame:
    """
    Simule ou extrait les ordres de bourse reçus dans la journée.
    Si la base DuckDB existe déjà, lit les données existantes, sinon génère un jeu de données de test.
    """
    logger.info("▶️ [Tâche 1/3] Démarrage de l'ingestion des ordres de bourse...")
    
    # Données d'ordres reçues (inclut un ordre Fat-Finger > 100k CHF pour tester la Compliance)
    data = [
        {"id_ordre": 1001, "client_id": "C-1082", "isin": "CH0012056047", "quantite": 500, "prix_unitaire_chf": 28.50, "date_ordre": "2026-10-30"},
        {"id_ordre": 1002, "client_id": "C-4421", "isin": "CH0038863350", "quantite": 120, "prix_unitaire_chf": 115.00, "date_ordre": "2026-10-30"},
        {"id_ordre": 1003, "client_id": "C-8841", "isin": "CH0012005267", "quantite": 1500, "prix_unitaire_chf": 95.00, "date_ordre": "2026-10-30"}, # 142,500 CHF (FAT FINGER)
        {"id_ordre": 1004, "client_id": "C-2290", "isin": "CH0012056047", "quantite": 200, "prix_unitaire_chf": 28.60, "date_ordre": "2026-10-30"}
    ]
    
    df = pd.DataFrame(data)
    
    # Calculs métiers des montants et frais
    df['montant_brut_chf'] = round(df['quantite'] * df['prix_unitaire_chf'], 2)
    df['frais_courtage_chf'] = round(df['montant_brut_chf'] * 0.0015, 4) # 0.15% de frais
    
    logger.info(f"✅ [Tâche 1/3] {len(df)} ordres de bourse chargés en mémoire.")
    return df


@task(name="Tache_2_Controle_Compliance_FINMA")
def task_controle_compliance(df_ordres: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Contrôle de conformité FINMA :
    - Isole les ordres > 100 000 CHF (Fat-Finger).
    - Déclenche une alerte immédiate pour chaque rejet.
    - Persiste les rejets dans la table 'table_rejets_compliance' de DuckDB.
    """
    logger.info("▶️ [Tâche 2/3] Exécution des filtres de conformité FINMA (Seuil: 100,000 CHF)...")
    
    SEUIL_FAT_FINGER = 100000.00
    
    # Séparation ordres valides / rejets
    df_rejets = df_ordres[df_ordres['montant_brut_chf'] > SEUIL_FAT_FINGER].copy()
    df_valides = df_ordres[df_ordres['montant_brut_chf'] <= SEUIL_FAT_FINGER].copy()
    
    if not df_rejets.empty:
        logger.warning(f"⚠️ DETECTED : {len(df_rejets)} ordre(s) non-conforme(s) détecté(s) !")
        
        # Enregistrement des rejets dans DuckDB pour l'audit trail
        con = duckdb.connect(DUCKDB_PATH)
        try:

            # 1. Supprime l'ancienne table obsolète pour repartir sur la nouvelle structure
            con.execute("DROP TABLE IF EXISTS table_rejets_compliance;")

            con.execute("""
                CREATE TABLE IF NOT EXISTS table_rejets_compliance (
                    id_ordre INT,
                    client_id VARCHAR,
                    isin VARCHAR,
                    montant_brut_chf DOUBLE,
                    motif_rejet VARCHAR,
                    date_rejet TIMESTAMP
                )
            """)
            
            for _, row in df_rejets.iterrows():
                motif = f"Fat-Finger (> {SEUIL_FAT_FINGER:,.0f} CHF)"
                
                # 1. Envoi de l'alerte en temps réel (Teams / Slack / Logs)
                envoyer_alerte_compliance(
                    id_ordre=int(row['id_ordre']),
                    client_id=str(row['client_id']),
                    montant_chf=float(row['montant_brut_chf']),
                    motif=motif
                )
                
                # 2. Insertion en base de données DWH
                con.execute("""
                    INSERT INTO table_rejets_compliance (id_ordre, client_id, isin, montant_brut_chf, motif_rejet, date_rejet)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (int(row['id_ordre']), str(row['client_id']), str(row['isin']), float(row['montant_brut_chf']), motif, datetime.now()))

        finally:
            con.close()
            
    logger.info(f"✅ [Tâche 2/3] Contrôle terminé : {len(df_valides)} ordres certifiés, {len(df_rejets)} rejet(s).")
    return df_valides, df_rejets


@task(name="Tache_3_Export_DataLake_et_DWH")
def task_export_data(df_valides: pd.DataFrame):
    """
    Exporte les transactions validées vers :
    1. Le fichier Data Lake Parquet (ordres_valides_2026.parquet)
    2. La table DuckDB 'table_ordres_bourse'
    """
    logger.info("▶️ [Tâche 3/3] Exportation des données certifiées vers Parquet et DuckDB...")
    
    if df_valides.empty:
        logger.warning("⚠️ Aucun ordre valide à exporter.")
        return
        
    # 1. Export Parquet (Data Lake)
    df_valides.to_parquet(PARQUET_CLEAN_PATH, index=False)
    logger.info(f"📄 Export Parquet réussi : {PARQUET_CLEAN_PATH}")
    
    # 2. Export DuckDB (Data Warehouse)
    con = duckdb.connect(DUCKDB_PATH)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS table_ordres_bourse AS SELECT * FROM df_valides WHERE 1=0;")
        con.execute("DELETE FROM table_ordres_bourse WHERE date_ordre = '2026-10-30';") # Idempotence
        con.execute("INSERT INTO table_ordres_bourse SELECT * FROM df_valides;")
        
        nb_rows = con.execute("SELECT COUNT(*) FROM table_ordres_bourse;").fetchone()[0]
        logger.info(f"🦆 Base DuckDB DWH mise à jour ({nb_rows} lignes au total dans 'table_ordres_bourse').")
    finally:
        con.close()

# -----------------------------------------------------------------------------
# 4. FLUX PRINCIPAL PREFECT (ORCHESTRATEUR FLOW)
# -----------------------------------------------------------------------------

@flow(name="Pipeline_ETL_Bancaire_Geneve")
def pipeline_etl_bancaire_master():
    """
    Orchestrateur Master du Pipeline Data Bancaire.
    """
    logger.info("==================================================================")
    logger.info("🚀 DÉMARRAGE DU PIPELINE ETL ORCHESTRÉ (PREFECT / DUCKDB / PARQUET)")
    logger.info("==================================================================")
    
    # Exécution séquentielle des tâches orchestrées
    df_raw = task_ingestion_ordres()
    df_valides, df_rejets = task_controle_compliance(df_raw)
    task_export_data(df_valides)
    
    logger.info("==================================================================")
    logger.info("🎉 PIPELINE ETL EXÉCUTÉ AVEC SUCCÈS (Audit Trail conforme FINMA)")
    logger.info("==================================================================")

if __name__ == '__main__':
    pipeline_etl_bancaire_master()