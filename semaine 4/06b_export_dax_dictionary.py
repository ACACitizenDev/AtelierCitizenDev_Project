import pandas as pd
import os

def generate_dax_dictionary():
    print("==================================================")
    print("📖 GÉNÉRATION DU DICTIONNAIRE DE MÉTADONNÉES DAX")
    print("==================================================\n")

    dax_catalog = [
        {
            "Nom_Mesure": "AuM Total CHF",
            "Table": "_Mesures",
            "Formule_DAX": "SUM(fact_ordres_bourse[montant_brut_chf])",
            "Description": "Total des capitaux engagés sur les ordres de bourse validés (CHF).",
            "Format": "Devise (CHF, 2 décimales)",
            "Conformite_FINMA": "Oui"
        },
        {
            "Nom_Mesure": "Total Ordres Executes",
            "Table": "_Mesures",
            "Formule_DAX": "COUNTROWS(fact_ordres_bourse)",
            "Description": "Nombre total de transactions boursières exécutées.",
            "Format": "Nombre entier",
            "Conformite_FINMA": "Oui"
        },
        {
            "Nom_Mesure": "Commissions Courtage CHF",
            "Table": "_Mesures",
            "Formule_DAX": "SUM(fact_ordres_bourse[frais_courtage_chf])",
            "Description": "Somme des frais de courtage prélevés par la banque (0.15%).",
            "Format": "Devise (CHF, 2 décimales)",
            "Conformite_FINMA": "Oui"
        },
        {
            "Nom_Mesure": "AuM YTD CHF",
            "Table": "_Mesures",
            "Formule_DAX": "TOTALYTD([AuM Total CHF], Dim_Date[Date])",
            "Description": "Cumul annuel glissant des AuM sur l'exercice en cours.",
            "Format": "Devise (CHF, 2 décimales)",
            "Conformite_FINMA": "Oui"
        },
        {
            "Nom_Mesure": "Variation MoM %",
            "Table": "_Mesures",
            "Formule_DAX": "DIVIDE([Variation MoM CHF], [AuM Mois Precedent], 0)",
            "Description": "Taux de croissance des AuM par rapport au mois précédent.",
            "Format": "Pourcentage (0.0%)",
            "Conformite_FINMA": "Oui"
        }
    ]

    df_catalog = pd.DataFrame(dax_catalog)
    
    output_path = os.path.join(os.path.dirname(__file__), "dictionnaire_dax_powerbi.csv")
    df_catalog.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ Dictionnaire de métadonnées généré avec succès dans : {output_path}")
    print(df_catalog[["Nom_Mesure", "Format", "Conformite_FINMA"]].to_string(index=False))

if __name__ == '__main__':
    generate_dax_dictionary()