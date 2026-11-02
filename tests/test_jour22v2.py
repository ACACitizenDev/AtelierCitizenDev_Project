import os
import re
import pytest

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS ET RACINE DU PROJET
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == 'tests' else SCRIPT_DIR

def find_file(filename):
    """Recherche un fichier à la racine du projet ou dans le dossier 'Semaine 5'."""
    path_root = os.path.join(ROOT_DIR, filename)
    path_script = os.path.join(SCRIPT_DIR, filename)
    path_semaine5 = os.path.join(ROOT_DIR, 'Semaine 5v2', filename)
    
    if os.path.exists(path_root): return path_root
    if os.path.exists(path_script): return path_script
    if os.path.exists(path_semaine5): return path_semaine5
    return None


def test_dockerfile_existence_and_content():
    """T22.1 : Vérifie la présence et la conformité des directives du Dockerfile."""
    dockerfile_path = os.path.join(ROOT_DIR, 'Dockerfile')
    assert os.path.exists(dockerfile_path), f"❌ Dockerfile introuvable dans : {ROOT_DIR}"
    
    with open(dockerfile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 💡 Détection flexible de l'image Python (ex: python:3.12-slim ou python:3.15-slim)
    assert re.search(r'FROM\s+python:3\.\d+(-slim)?', content, re.IGNORECASE), \
        "❌ Directive 'FROM python:3.x-slim' manquante ou invalide dans le Dockerfile."
    
    # Vérification des répertoires et commandes clés
    assert 'WORKDIR /app' in content, "❌ Directive 'WORKDIR /app' manquante dans le Dockerfile."
    assert 'COPY requirements.txt' in content, "❌ Directive 'COPY requirements.txt' manquante dans le Dockerfile."
    assert 'CMD' in content, "❌ Directive d'exécution 'CMD' manquante dans le Dockerfile."


def test_docker_compose_volume_configuration():
    """T22.2 : Vérifie la configuration du volume persistant dans docker-compose.yml."""
    compose_path = os.path.join(ROOT_DIR, 'docker-compose.yml')
    assert os.path.exists(compose_path), f"❌ docker-compose.yml introuvable dans : {ROOT_DIR}"
    
    with open(compose_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'services:' in content, "❌ Section 'services:' manquante dans docker-compose.yml."
    assert 'volumes:' in content, "❌ Section 'volumes:' manquante dans docker-compose.yml."
    assert 'Base de donnée' in content or 'Base de donnee' in content, \
        "❌ Le montage de volume persistant pour la base de données est manquant dans docker-compose.yml."


def test_streamlit_app_file_exists():
    """T22.3 : Vérifie la présence du script d'interface Streamlit."""
    streamlit_path = find_file('05c_app_streamlit.py')
    assert streamlit_path is not None and os.path.exists(streamlit_path), \
        "❌ Script d'interface Streamlit '05c_app_streamlit.py' introuvable."