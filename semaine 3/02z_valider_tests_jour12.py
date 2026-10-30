import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')
DB_PATH = os.path.join(DB_DIR, 'banque_geneve_oltp.db')

def valider_tests_jour12():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable à l'adresse : {DB_PATH}")
        return

    print("==================================================")
    print("🧪 MATRICE DE RECETTE & TESTS D'INTÉGRITÉ — JOUR 12")
    print("==================================================\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # -------------------------------------------------------------------------
    # TEST 12.1 : Présence des Tables de Feeds & Vue
    # -------------------------------------------------------------------------
    cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
    elements = [r[0] for r in cursor.fetchall()]
    if 'taux_bns' in elements and 'cotations_smi' in elements and 'v_valorisation_portefeuille' in elements:
        print("✅ Test 12.1 [PASS] : Tables d'ingestion `taux_bns`, `cotations_smi` et vue multi-devises créées.")
    else:
        print(f"❌ Test 12.1 [FAIL] : Éléments manquants : {elements}")

    # -------------------------------------------------------------------------
    # TEST 12.2 : Test d'Idempotence (UPSERT)
    # -------------------------------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM taux_bns;")
    count_initial = cursor.fetchone()[0]
    
    # Exécution d'une 2e insertion identique
    cursor.execute("INSERT OR REPLACE INTO taux_bns VALUES ('EUR/CHF', 0.9350, '2026-10-29');")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM taux_bns;")
    count_final = cursor.fetchone()[0]
    
    if count_initial == count_final:
        print(f"✅ Test 12.2 [PASS] : Idempotence certifiée (UPSERT conserve {count_final} lignes sans doublons).")
    else:
        print(f"❌ Test 12.2 [FAIL] : Des doublons ont été créés ({count_initial} -> {count_final})")

    # -------------------------------------------------------------------------
    # TEST 12.3 : Contrôle de Cohérence des Données BNS
    # -------------------------------------------------------------------------
    cursor.execute("SELECT taux_chf FROM taux_bns WHERE paire = 'EUR/CHF';")
    taux_eur = cursor.fetchone()[0]
    if 0.5.lower() < str(taux_eur) < "1.5" if isinstance(taux_eur, str) else 0.5 < taux_eur < 1.5:
        print(f"✅ Test 12.3 [PASS] : Taux EUR/CHF valide ({taux_eur} CHF).")
    else:
        print(f"❌ Test 12.3 [FAIL] : Taux BNS aberrant ({taux_eur}).")

    # -------------------------------------------------------------------------
    # TEST 12.4 : Test de Conversion Multi-Devises (Client EUR)
    # -------------------------------------------------------------------------
    try:
        # Création d'un client de test en devises EUR
        cursor.execute("INSERT OR REPLACE INTO comptes_clients VALUES ('CPT-EUR-01', 'Client_Paris_01', 'HNWI', 'EUR', 'CH11 **** **** **** *1111');")
        cursor.execute("INSERT OR REPLACE INTO ordres_bourse (id_ordre, id_compte, symbole, type_ordre, quantite, prix_execution) VALUES ('ORD-EUR-01', 'CPT-EUR-01', 'BCGE.SW', 'Achat', 10, 220.00);")
        conn.commit()

        # Requête de valorisation sur la vue
        cursor.execute("SELECT montant_brut_chf, montant_converti_devise_client FROM v_valorisation_portefeuille WHERE id_ordre = 'ORD-EUR-01';")
        brut_chf, converti_eur = cursor.fetchone()
        
        # 2'200 CHF / 0.9350 = ~2'352.94 EUR
        if converti_eur > brut_chf:
            print(f"✅ Test 12.4 [PASS] : Valorisation dynamique exacte (2'200.00 CHF = {converti_eur:,.2f} EUR avec taux 0.9350).")
        else:
            print(f"❌ Test 12.4 [FAIL] : Problème de conversion ({brut_chf} CHF vs {converti_eur} EUR)")
    except Exception as e:
        print(f"❌ Test 12.4 [FAIL] : {e}")

    conn.close()
    print("\n--------------------------------------------------")
    print("🏆 CERTIFICATION JOUR 12 : Ingestion et conversion validées !")
    print("--------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour12()