import os
import sys
import subprocess

# -----------------------------------------------------------------------------
# DÉTERMINATION DES CHEMINS (RACINE ET DOSSIER DU SCRIPT)
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5', 'semaine_5', 'semaine5']:
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
else:
    ROOT_DIR = SCRIPT_DIR

def find_tests_file():
    """Recherche test_quality_gates.py à la racine ou dans le sous-dossier."""
    path_root = os.path.join(ROOT_DIR, 'tests', 'test_quality_gates.py')
    path_script = os.path.join(SCRIPT_DIR, 'tests', 'test_quality_gates.py')
    
    if os.path.exists(path_root):
        return path_root, os.path.join(ROOT_DIR, 'tests')
    elif os.path.exists(path_script):
        return path_script, os.path.join(SCRIPT_DIR, 'tests')
    return None, None

def valider_tests_jour23():
    print("==================================================")
    print("🧪 RECETTE & CERTIFICATION SEMAINE 5 — JOUR 23")
    print("==================================================\n")

    # 1. Vérification du fichier de tests
    test_file_path, tests_dir = find_tests_file()
    
    if test_file_path:
        print(f"✅ Test 23.1 [PASS] : Fichier de tests détecté ({test_file_path}).")
    else:
        print(f"❌ Test 23.1 [FAIL] : Fichier 'test_quality_gates.py' introuvable dans {os.path.join(ROOT_DIR, 'tests')} ni {os.path.join(SCRIPT_DIR, 'tests')}.")
        return

    # 2. Vérification de la configuration GitHub Actions
    path_wf_root = os.path.join(ROOT_DIR, '.github', 'workflows', 'ci_pipeline.yml')
    path_wf_script = os.path.join(SCRIPT_DIR, '.github', 'workflows', 'ci_pipeline.yml')
    
    if os.path.exists(path_wf_root) or os.path.exists(path_wf_script):
        print("✅ Test 23.2 [PASS] : Workflow GitHub Actions ci_pipeline.yml configuré.")
    else:
        print("⚠️ Test 23.2 [WARNING] : Workflow GitHub Actions non détecté (Optionnel pour validation locale).")

    # 3. Exécution programmatique de PyTest
    try:
        res = subprocess.run([sys.executable, "-m", "pytest", tests_dir, "-q"], capture_output=True, text=True)
        if res.returncode == 0:
            print("✅ Test 23.3 [PASS] : 100% des assertions PyTest sont passées au vert !")
        else:
            print(f"❌ Test 23.3 [FAIL] : Échec de la suite PyTest :\n{res.stdout}\n{res.stderr}")
    except Exception as e:
        print(f"❌ Test 23.3 [FAIL] : Impossible d'exécuter PyTest : {e}")

    print("\n------------------------------------------------------------------")
    print("🎉 CERTIFICATION JOUR 23 ACHEVÉE !")
    print("------------------------------------------------------------------")

if __name__ == '__main__':
    valider_tests_jour23()