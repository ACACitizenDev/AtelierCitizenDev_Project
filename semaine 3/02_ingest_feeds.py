import sqlite3
import os
import json
from datetime import date, datetime

# Configuration du chemin vers le dossier 'Base de donnée'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')

def ingest_financial_feeds():
    print(f"📍 Connexion à la base pour ingestion : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # =========================================================================
    # 1. CRÉATION DES TABLES D'INGESTION
    # =========================================================================
    
    # Table A : Taux de change BNS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS taux_bns (
        paire TEXT PRIMARY KEY,
        taux_chf REAL NOT NULL CHECK(taux_chf > 0),
        date_valeur TEXT NOT NULL
    );
    """)

    # Table B : Cotations de Marché SMI (SIX Swiss Exchange)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cotations_smi (
        symbole TEXT PRIMARY KEY,
        dernier_cours_chf REAL NOT NULL CHECK(dernier_cours_chf > 0),
        volume_echange INTEGER NOT NULL CHECK(volume_echange >= 0),
        date_mise_a_jour DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (symbole) REFERENCES referentiel_titres(symbole) ON DELETE RESTRICT
    );
    """)

    # =========================================================================
    # 2. SIMULATION DE PAYLOADS JSON (Simule le retour des APIs BNS & SIX)
    # =========================================================================
    
    # Taux officiels du jour BNS (1 EUR = 0.9350 CHF, 1 USD = 0.8620 CHF)
    payload_bns_json = """
    [
        {"pair": "EUR/CHF", "rate": 0.9350, "date": "2026-10-29"},
        {"pair": "USD/CHF", "rate": 0.8620, "date": "2026-10-29"},
        {"pair": "GBP/CHF", "rate": 1.1210, "date": "2026-10-29"}
    ]
    """

    # Feeds temps réel des actions suisses
    payload_smi_json = """
    [
        {"ticker": "BCGE.SW", "price": 220.00, "volume": 14500},
        {"ticker": "UBSG.SW", "price": 28.50, "volume": 1250000}
    ]
    """

    # =========================================================================
    # 3. PARSING & INGESTION IDEMPOTENTE (UPSERT)
    # =========================================================================
    
    # A. Ingestion Taux BNS
    data_bns = json.loads(payload_bns_json)
    for item in data_bns:
        cursor.execute("""
        INSERT OR REPLACE INTO taux_bns (paire, taux_chf, date_valeur)
        VALUES (?, ?, ?);
        """, (item["pair"], item["rate"], item["date"]))
    
    print(f"✅ Ingestion BNS : {len(data_bns)} paires de devises enregistrées/mises à jour.")

    # B. Ingestion Cotations SMI
    data_smi = json.loads(payload_smi_json)
    for item in data_smi:
        cursor.execute("""
        INSERT OR REPLACE INTO cotations_smi (symbole, dernier_cours_chf, volume_echange, date_mise_a_jour)
        VALUES (?, ?, ?, ?);
        """, (item["ticker"], item["price"], item["volume"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    print(f"✅ Ingestion SMI : {len(data_smi)} cotations enregistrées/mises à jour.")

    # =========================================================================
    # 4. CREATION DE LA VUE CONSOLIDÉE DE VALORISATION MULTI-DEVISES
    # =========================================================================
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS v_valorisation_portefeuille AS
    SELECT 
        o.id_ordre,
        o.id_compte,
        c.nom_client_anonyme,
        c.devise_ref AS devise_client,
        o.symbole,
        o.quantite,
        o.prix_execution AS prix_chf,
        o.montant_brut_chf,
        
        -- Conversion dynamique selon le taux BNS si le client est en EUR
        CASE 
            WHEN c.devise_ref = 'EUR' THEN ROUND(o.montant_brut_chf / (SELECT taux_chf FROM taux_bns WHERE paire = 'EUR/CHF'), 2)
            WHEN c.devise_ref = 'USD' THEN ROUND(o.montant_brut_chf / (SELECT taux_chf FROM taux_bns WHERE paire = 'USD/CHF'), 2)
            ELSE o.montant_brut_chf
        END AS montant_converti_devise_client
    FROM ordres_bourse o
    INNER JOIN comptes_clients c ON o.id_compte = c.id_compte;
    """)

    conn.commit()
    conn.close()
    print("✅ Vue de valorisation multi-devises (v_valorisation_portefeuille) créée.")

if __name__ == '__main__':
    ingest_financial_feeds()