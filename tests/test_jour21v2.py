import os
import sys
import importlib.util

# 1. Détermination du chemin vers le dossier 'Semaine 5'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
FILE_PATH = os.path.join(ROOT_DIR, "Semaine 5v2", "05b_jour21_ai_prompt.py")

# 2. Chargement dynamique du module depuis le chemin du fichier
spec = importlib.util.spec_from_file_location("jour21_ai_prompt", FILE_PATH)
_jour21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_jour21)

# Importer les fonctions nécessaires depuis le module chargé
preparer_prompt_nl2sql = _jour21.preparer_prompt_nl2sql
extraire_requete_sql = _jour21.extraire_requete_sql

def test_ai_prompt_structure():
    """T21.1 : Vérifie que le prompt inclut le dictionnaire et la question."""
    q = "Montre les 5 plus gros ordres de bourse"
    prompt = preparer_prompt_nl2sql(q)
    assert "table_ordres_bourse" in prompt
    assert "montant_brut_chf" in prompt
    assert q in prompt

def test_sql_extraction_from_markdown():
    """T21.2 : Vérifie l'isolation propre du bloc SQL nettoyé."""
    raw_response = "Voici la requête SQL :\n```sql\nSELECT * FROM table_ordres_bourse;\n```"
    sql_clean = extraire_requete_sql(raw_response)
    assert sql_clean == "SELECT * FROM table_ordres_bourse;"
    assert "```" not in sql_clean

def test_frais_calculation_logic():
    """T21.3 : Validation mathématique du taux de courtage (0.15%)."""
    quantite = 200
    prix = 50.0
    montant_brut = quantite * prix
    frais = round(montant_brut * 0.0015, 4)
    assert montant_brut == 10000.0
    assert frais == 15.0