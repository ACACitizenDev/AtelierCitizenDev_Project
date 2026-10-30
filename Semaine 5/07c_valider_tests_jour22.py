import os
import sys

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS (RACINE DU PROJET ET DOSSIER LOCAL)
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Si le script est exécuté depuis le sous-dossier 'semaine 5', la racine est le dossier parent
if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5', 'semaine_5', 'semaine5']:
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
else:
    ROOT_DIR = SCRIPT_DIR

def find_file(filename):
    """Recherche un fichier à la racine du projet ou dans le dossier du script."""
    path_root = os.path.join(ROOT_DIR, filename)
    path_script = os.path.join(SCRIPT_DIR, filename)
    
    if os.path.exists(path_root):
        return path_root
    elif os.path.exists(path_script):
        return path_script
    return None

def valider_tests_jour22():
    print("==================================================")
    print("🧪 RECETTE & CERTIFICATION SEMAINE 5 — JOUR 22")
    print("==================================================\n")

    # 1. Vérification du Dockerfile
    dockerfile_path = find_file('Dockerfile')
    if dockerfile_path:
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'FROM python:' in content and 'WORKDIR /app' in content:
                print(f"✅ Test 22.1 [PASS] : Dockerfile conforme ({dockerfile_path}).")
            else:
                print(f"⚠️ Test 22.1 [WARNING] : Dockerfile présent mais directives 'FROM' / 'WORKDIR' à revoir.")
    else:
        print(f"❌ Test 22.1 [FAIL] : Fichier Dockerfile introuvable dans {ROOT_DIR} ni {SCRIPT_DIR}.")

    # 2. Vérification du fichier docker-compose.yml
    compose_path = find_file('docker-compose.yml')
    if compose_path:
        with open(compose_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'volumes:' in content and 'Base de donnée' in content:
                print(f"✅ Test 22.2 [PASS] : docker-compose.yml conforme avec volume persistant ({compose_path}).")
            else:
                print(f"⚠️ Test 22.2 [WARNING] : docker-compose.yml présent mais volume non détecté.")
    else:
        print(f"❌ Test 22.2 [FAIL] : Fichier docker-compose.yml introuvable dans {ROOT_DIR} ni {SCRIPT_DIR}.")

    # 3. Vérification du fichier .dockerignore
    ignore_path = find_file('.dockerignore')
    if ignore_path:
        print(f"✅ Test 22.3 [PASS] : Fichier .dockerignore présent ({ignore_path}).")
    else:
        print("⚠️ Test 22.3 [WARNING] : Fichier .dockerignore recommandé mais absent.")

    # 4. Vérification du fichier requirements.txt
    req_path = find_file('requirements.txt')
    if req_path:
        print(f"✅ Test 22.4 [PASS] : Fichier requirements.txt détecté ({req_path}).")
    else:
        print(f"❌ Test 22.4 [FAIL] : Fichier requirements.txt introuvable dans {ROOT_DIR} ni {SCRIPT_DIR}.")

    print("\n------------------------------------------------------------------")
    print("🎉 CERTIFICATION JOUR 22 ACHEVÉE !")
    print("------------------------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour22()