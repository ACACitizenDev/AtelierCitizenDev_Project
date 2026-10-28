import os
import pandas as pd
from datetime import datetime

# 1. Définition du chemin de sortie
user_profile = os.environ.get('USERPROFILE', '')
target_dir = os.path.join(user_profile, 'CitizenDev_Environment', 'data')
os.makedirs(target_dir, exist_ok=True)
csv_filepath = os.path.join(target_dir, 'taux_bns.csv')

print(f"[{datetime.now()}] Initialisation de l'extraction des taux BNS...")

# 2. Simulation de données de taux (ou extraction via pandas read_html)
data_taux = {
    'Devise': ['EUR/CHF', 'USD/CHF', 'GBP/CHF', 'JPY/CHF'],
    'Taux_Indicatif': [0.9345, 0.8620, 1.1210, 0.5640],
    'Date_Mise_A_Jour': [datetime.now().strftime('%Y-%m-%d')] * 4,
    'Source': ['Banque Nationale Suisse'] * 4
}

df_taux = pd.DataFrame(data_taux)

# 3. Export CSV structuré au format Suisse (séparateur ;)
df_taux.to_csv(csv_filepath, sep=';', index=False, encoding='utf-8-sig')

print(f"[{datetime.now()}] Succès : Fichier généré avec succès dans {csv_filepath}")