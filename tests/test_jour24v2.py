import os
import sys
import pytest
import pandas as pd
import importlib.util

# =============================================================================
# 1. DÉTERMINATION ET CONFIGURATION DES CHEMINS D'ACCÈS (SYSTEM PATHS)
# =============================================================================

# Récupère le chemin absolu du dossier contenant ce fichier de test (ex: .../AtelierCitizenDev_Project/tests)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Détermine la racine du projet : si le dossier courant est 'tests', on remonte d'un cran
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'tests' else SCRIPT_DIR

# Définition des chemins absolus vers les répertoires cibles des scripts à tester
SEMAINE5_DIR = os.path.join(ROOT_DIR, "Semaine 5")
SEMAINE5V2_DIR = os.path.join(ROOT_DIR, "Semaine 5v2")

# Ajout dynamique de ces sous-dossiers au sys.path de Python pour autoriser les imports croisés (ex: 07_logger_config)
for path in [SEMAINE5_DIR, SEMAINE5V2_DIR, ROOT_DIR]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# =============================================================================
# 2. CHARGEUR DYNAMIQUE DE MODULES DEPUIS N'IMPORTE QUEL SOUS-DOSSIER
# =============================================================================

def load_module_from_file(module_name, relative_path):
    """Charge dynamiquement un script Python à partir de son chemin relatif."""
    # Construit le chemin d'accès absolu au fichier cible
    full_path = os.path.join(ROOT_DIR, relative_path)
    
    # Sécurité fallback au cas où le script est exécuté depuis un répertoire courant différent
    if not os.path.exists(full_path):
        full_path = os.path.join(SCRIPT_DIR, "..", relative_path)
    
    # Vérifie physiquement l'existence du fichier avant toute tentative d'importation
    assert os.path.exists(full_path), f"❌ Fichier introuvable : {full_path}"
    
    # Spécification et création de l'objet module via importlib
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    
    # Exécution du module pour charger ses fonctions et variables en mémoire
    spec.loader.exec_module(mod)
    return mod

# =============================================================================
# 3. INSTANCIATION DES MODULES CIBLES (SEMAINE 5 ET SEMAINE 5V2)
# =============================================================================

# Chargement du script 07f_alert_notifier.py situé dans le dossier "Semaine 5"
alert_mod = load_module_from_file("alert_notifier", os.path.join("Semaine 5", "07f_alert_notifier.py"))

# Chargement du script 05e_plotly_engine.py situé dans le dossier "Semaine 5v2"
plotly_mod = load_module_from_file("plotly_engine", os.path.join("Semaine 5v2", "05e_plotly_engine.py"))

# =============================================================================
# 4. SUITE DE TESTS UNITAIRES ET D'INTÉGRATION (PYTEST JOUR 24)
# =============================================================================

def test_alert_notifier_existence_and_function():
    """T24.1 : Vérifie le bon déclenchement du module d'alerting (Semaine 5)."""
    # Vérifie que la fonction 'envoyer_alerte_compliance' est bien définie dans le module chargé
    assert hasattr(alert_mod, 'envoyer_alerte_compliance'), "❌ Fonction 'envoyer_alerte_compliance' manquante dans 07f_alert_notifier.py"
    
    # Exécute la fonction avec un cas d'usage réel (Ordre boursier Fat-Finger > 100k CHF)
    res = alert_mod.envoyer_alerte_compliance(
        id_ordre=9999, 
        client_id="C-TEST-J24", 
        montant_chf=150000.0, 
        motif="Test Unitaire PyTest"
    )
    
    # Confirme que la fonction s'exécute avec succès sans levée d'erreur et renvoie True
    assert res is True, "❌ L'envoi d'alerte de conformité a renvoyé un résultat négatif."


def test_plotly_engine_bar_chart_generation():
    """T24.2 : Vérifie la création dynamique d'un visuel Plotly (Semaine 5v2)."""
    # Vérifie la présence de la fonction 'generer_visuel_dynamique' dans le module chargé
    assert hasattr(plotly_mod, 'generer_visuel_dynamique'), "❌ Fonction 'generer_visuel_dynamique' manquante dans 05e_plotly_engine.py"
    
    # Crée un DataFrame Pandas de simulation à 2 colonnes (Segment client vs AuM en CHF)
    df_sample = pd.DataFrame({
        "segment_client": ["UHNWI", "HNWI"],
        "total_aum_chf": [2500000.0, 750000.0]
    })
    
    # Appel de la fonction pour générer l'objet graphique
    fig = plotly_mod.generer_visuel_dynamique(df_sample, titre="Test AuM Segment")
    
    # Vérifie que la fonction n'a pas renvoyé None pour des données valides
    assert fig is not None, "❌ Le moteur Plotly n'a produit aucun graphique pour un jeu de données valide."
    
    # Vérifie que l'objet retourné est bien une Figure Plotly disposant d'un attribut 'layout'
    assert hasattr(fig, 'layout'), "❌ L'objet retourné n'est pas une figure Plotly valide."


def test_plotly_engine_empty_dataframe_handling():
    """T24.3 : Vérifie la gestion robuste d'un DataFrame vide par le moteur Plotly."""
    # Instanciation d'un DataFrame Pandas totalement vide
    df_empty = pd.DataFrame()
    
    # Transmission du DataFrame vide au moteur de visualisation Plotly
    fig = plotly_mod.generer_visuel_dynamique(df_empty, titre="Test Vide")
    
    # Valide le comportement défensif : le moteur doit retourner None sans faire planter l'application
    assert fig is None, "❌ Le moteur Plotly devrait renvoyer None lorsqu'un DataFrame vide est transmis."
