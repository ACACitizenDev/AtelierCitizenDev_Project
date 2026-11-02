import os
import duckdb

DWH_DICTIONARY_SCHEMA = """
=== DICTIONNAIRE DE DONNÉES DUCKDB (BANQUE PRIVÉE GENÈVE) ===
Table 'table_ordres_bourse' :
  - id_ordre (INT) : Identifiant unique de la transaction
  - client_id (VARCHAR) : Identifiant client
  - isin (VARCHAR) : Code ISIN du titre financier (ex: CH0012056047)
  - quantite (INT) : Nombre de titres
  - prix_unitaire_chf (DOUBLE) : Cours d'exécution en CHF
  - montant_brut_chf (DOUBLE) : Montant total transactionnel en CHF
  - frais_courtage_chf (DOUBLE) : Frais de courtage (0.15%)
  - date_ordre (DATE) : Date de valeur de l'ordre

Consigne strictes pour l'agent IA :
1. Générer uniquement une requête SQL DuckDB valide.
2. La requête doit impérativement commencer par 'SELECT'.
3. Ne pas ajouter d'explications de texte en dehors du SQL.
"""

def preparer_prompt_nl2sql(question_utilisateur: str) -> str:
    """
    Construit le prompt complet prêt pour l'inférence du LLM / Agent IA.
    """
    return f"{DWH_DICTIONARY_SCHEMA}\nQuestion de l'utilisateur : \"{question_utilisateur}\"\nRequête SQL :"

def extraire_requete_sql(reponse_llm: str) -> str:
    """
    Nettoie et isole la requête SQL d'une réponse LLM.
    """
    cleaned = reponse_llm.strip()
    if "```sql" in cleaned:
        cleaned = cleaned.split("```sql")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    return cleaned

if __name__ == '__main__':
    prompt_demo = preparer_prompt_nl2sql("Donne-moi le montant total par client pour l'année 2026")
    print("--- PROMPT FORMATÉ JOUR 21 ---")
    print(prompt_demo)