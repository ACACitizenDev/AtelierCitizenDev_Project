import sqlite3
import os

from duckdb import cursor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')

def init_sqlite_oltp():
    print(f"📍 Création/Connexion à la base : {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ⚠️ CRITIQUE : Activation explicite du contrôle des clés étrangères dans SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. SUPPRESSION DE TOUTES LES VUES (Jour 11 & Jour 12)
    cursor.execute("DROP VIEW IF EXISTS v_valorisation_portefeuille;")
    cursor.execute("DROP VIEW IF EXISTS v_ordres_bourse_details;")

    # 3. SUPPRESSION DE TOUTES LES TABLES (Jour 11 & Jour 12)
    cursor.execute("DROP TABLE IF EXISTS cotations_smi;")
    cursor.execute("DROP TABLE IF EXISTS taux_bns;")
    cursor.execute("DROP TABLE IF EXISTS ordres_bourse;")
    cursor.execute("DROP TABLE IF EXISTS comptes_clients;")
    cursor.execute("DROP TABLE IF EXISTS referentiel_titres;")

    # =========================================================================
    # 1. TABLE : COMPTES CLIENTS (Conformité nLPD Suisse)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comptes_clients (
        id_compte TEXT PRIMARY KEY,
        nom_client_anonyme TEXT NOT NULL,
        segment_client TEXT CHECK(segment_client IN ('HNWI', 'UHNWI', 'Retail', 'Institutional')),
        devise_ref TEXT DEFAULT 'CHF',
        iban_anonymise TEXT NOT NULL CHECK(iban_anonymise LIKE '____ **** **** **** *____')
    );
    """)

    # =========================================================================
    # 2. TABLE : RÉFÉRENTIEL TITRES (Bourse Suisse - SIX)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referentiel_titres (
        symbole TEXT PRIMARY KEY,
        nom_societe TEXT NOT NULL,
        isin TEXT UNIQUE NOT NULL CHECK(length(isin) = 12),
        place_boursiere TEXT DEFAULT 'SIX Swiss Exchange',
        devise TEXT DEFAULT 'CHF'
    );
    """)

    # =========================================================================
    # 3. TABLE : ORDRES BOURSE (Transactionnel & Colonnes Calculées)
    # =========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordres_bourse (
        id_ordre TEXT PRIMARY KEY,
        id_compte TEXT NOT NULL,
        symbole TEXT NOT NULL,
        type_ordre TEXT CHECK(type_ordre IN ('Achat', 'Vente')),
        quantite INTEGER NOT NULL CHECK(quantite > 0),
        prix_execution REAL NOT NULL CHECK(prix_execution > 0),
        
        -- Colonnes générées automatiquement par le moteur SQLite (ACID)
        montant_brut_chf REAL GENERATED ALWAYS AS (quantite * prix_execution) STORED,
        frais_courtage_chf REAL GENERATED ALWAYS AS (quantite * prix_execution * 0.0015) STORED,
        
        statut_ordre TEXT DEFAULT 'Nouveau' CHECK(statut_ordre IN ('Nouveau', 'Transmis', 'Execute', 'Rejete')),
        horodatage DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        -- Contraintes de clés étrangères (FK)
        FOREIGN KEY (id_compte) REFERENCES comptes_clients(id_compte) ON DELETE RESTRICT,
        FOREIGN KEY (symbole) REFERENCES referentiel_titres(symbole) ON DELETE RESTRICT
    );
    """)

    # Indexation B-Tree pour optimiser les requêtes de recherche et jointures
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ordres_compte ON ordres_bourse(id_compte);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ordres_symbole ON ordres_bourse(symbole);")

    # =========================================================================
    # 5. BLOC AJOUTÉ : CRÉATION DE LA VUE SQL (DÉTAILS COMPLETS ENRICHIS)
    # =========================================================================
    cursor.execute("""
    CREATE VIEW v_ordres_bourse_details AS
    SELECT 
        o.id_ordre,
        o.id_compte,
        c.nom_client_anonyme,
        c.iban_anonymise,
        o.symbole,
        t.nom_societe,
        o.type_ordre,
        o.quantite,
        o.prix_execution,
        o.montant_brut_chf,
        o.frais_courtage_chf,
        o.statut_ordre,
        o.horodatage
    FROM ordres_bourse o
    INNER JOIN comptes_clients c ON o.id_compte = c.id_compte
    INNER JOIN referentiel_titres t ON o.symbole = t.symbole;
    """)

    # =========================================================================
    # INGESTION DES DONNÉES DE RÉFÉRENCE (IDEMPOTENCE)
    # =========================================================================
    cursor.execute("""
    INSERT OR REPLACE INTO comptes_clients 
    VALUES ('CPT-1001', 'Client_GVA_001', 'UHNWI', 'CHF', 'CH68 **** **** **** *6789');
    """)
    
    cursor.execute("""
    INSERT OR REPLACE INTO comptes_clients 
    VALUES ('CPT-1002', 'Client_GVA_002', 'HNWI', 'CHF', 'CH93 **** **** **** *1234');
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO comptes_clients 
    VALUES ('CPT-1003', 'Client_GVA_003', 'HNWI', 'CHF', 'CH93 **** **** **** *5678');
    """)
    cursor.execute("""
    INSERT OR REPLACE INTO comptes_clients 
    VALUES ('CPT-1004', 'Client_GVA_004', 'HNWI', 'CHF', 'CH74 **** **** **** *0503');
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO referentiel_titres 
    VALUES ('BCGE.SW', 'Banque Cantonale de Genève', 'CH0002177767', 'SIX Swiss Exchange', 'CHF');
    """)
    
    cursor.execute("""
    INSERT OR REPLACE INTO referentiel_titres 
    VALUES ('UBSG.SW', 'UBS Group AG', 'CH0244767585', 'SIX Swiss Exchange', 'CHF');
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO referentiel_titres 
    VALUES ('NESN.SW', 'NESTLÉ N', 'CH0038863350', 'SIX Swiss Exchange', 'CHF');
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO referentiel_titres 
    VALUES ('NOVN.SW', 'NOVARTIS N', 'CH0012005267', 'SIX Swiss Exchange', 'CHF');
    """)
    
    cursor.execute("""
    INSERT OR REPLACE INTO referentiel_titres 
    VALUES ('TOGN.SW', 'DUMMY AG', 'CH9999999999', 'SIX Swiss Exchange', 'CHF');
    """)

    cursor.executemany("""
    INSERT OR REPLACE INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution, statut_ordre)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, [
        ('ORD-2026-001', 'CPT-1001', 'NESN.SW', 'Achat', 150, 95.50, 'Execute'),      # ~14'325 CHF
        ('ORD-2026-002', 'CPT-1002', 'NOVN.SW', 'Achat', 200, 88.20, 'Execute'),      # ~17'640 CHF
        ('ORD-2026-003', 'CPT-1003', 'TOGN.SW', 'Vente', 50, 310.00, 'Execute'),      # ~15'500 CHF
        ('ORD-2026-004', 'CPT-1001', 'BCGE.SW', 'Achat', 100, 205.00, 'Execute'),     # ~20'500 CHF
        ('ORD-2026-005', 'CPT-1004', 'UBSG.SW', 'Achat', 1000, 28.40, 'Execute')      # ~28'400 CHF
    ])

    conn.commit()
    conn.close()
    print("✅ Base OLTP SQLite initialisée avec succès : banque_geneve_oltp.db")

if __name__ == '__main__':
    init_sqlite_oltp()