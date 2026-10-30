import sqlite3

# Connexion à la base
conn = sqlite3.connect('banque_geneve_oltp.db')
cursor = conn.cursor()

# Tapez votre requête SQL ici
req = """
SELECT * FROM comptes_clients;
"""

cursor.execute(req)

# Si c'est un SELECT, afficher les résultats
if req.strip().upper().startswith("SELECT"):
    for row in cursor.fetchall():
        print(row)
else:
    conn.commit()
    print("✅ Requête exécutée et sauvegardée.")

conn.close()