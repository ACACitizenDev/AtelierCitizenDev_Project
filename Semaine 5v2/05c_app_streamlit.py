import os
import sys
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px

# =============================================================================
# 1. CONFIGURATION DE LA PAGE STREAMLIT
# =============================================================================
st.set_page_config(
    page_title="Copilot IA — Données Réelles DuckDB",
    page_icon="🏦",
    layout="wide"
)








SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
DB_DIR = os.path.join(PARENT_DIR, 'Base de donnée')

DUCKDB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')
PARQUET_CLEAN_PATH = os.path.join(DB_DIR, 'ordres_valides_2026.parquet')

def run_quality_engineering():
    print(f"📍 Connexion au Data Warehouse DuckDB : {DUCKDB_PATH}")
    
    if not os.path.exists(DUCKDB_PATH):
        print("❌ Erreur : Le fichier DuckDB est introuvable. Exécutez le Jour 13 d'abord.")
        return

    con = duckdb.connect(DUCKDB_PATH)



# =============================================================================
# 2. RÉSOLUTION DES CHEMINS ET CONNEXION DUCKDB RÉELLE
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5v2', 'semaine_5v2', 'semaine5v2'] else SCRIPT_DIR
DB_DIR = os.path.join(ROOT_DIR, 'Base de donnée')
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, 'banque_geneve_dwh.duckdb')

def get_duckdb_connection(read_only=True):
    """Établit une connexion avec la base physique DuckDB si elle existe."""
    if os.path.exists(DB_PATH):
        try:
            return duckdb.connect(DB_PATH, read_only=read_only), True
        except Exception as e:
            st.error(f"Erreur de connexion à DuckDB : {e}")
            return None, False
    return None, False

# =============================================================================
# 3. MOTEUR DE REQUÊTES EN LANGAGE NATUREL (NL2SQL RÉEL SUR DUCKDB)
# =============================================================================
def executer_requete_duckdb_reelle(question: str) -> tuple[str, pd.DataFrame, str]:
    """
    Exécute les vraies requêtes SQL sur les tables physiques DuckDB.
    """
    con, is_ok = get_duckdb_connection(read_only=True)
    if not is_ok or con is None:
        return "-- Base DuckDB non trouvée", pd.DataFrame(), "DISCONNECTED"

    try:
        # Vérification des tables existantes dans la base réelle
        tables_df = con.execute("SHOW TABLES;").df()
        tables_list = tables_df['name'].tolist() if not tables_df.empty else []

        if 'table_ordres_bourse' not in tables_list:
            con.close()
            return "-- Table 'table_ordres_bourse' manquante dans le DWH", pd.DataFrame(), "NO_TABLE"

        q_lower = question.lower()
        
        # Moteur de règles SQL orienté DWH
        if "segment" in q_lower or "client" in q_lower:
            sql = """
            SELECT client_id, 
                   COUNT(id_ordre) as total_ordres, 
                   ROUND(SUM(montant_brut_chf), 2) as total_aum_chf,
                   ROUND(SUM(frais_courtage_chf), 2) as total_frais_chf
            FROM table_ordres_bourse 
            GROUP BY client_id 
            ORDER BY total_aum_chf DESC 
            LIMIT 15;
            """
        elif "frais" in q_lower or "date" in q_lower:
            sql = """
            SELECT date_ordre, 
                   COUNT(id_ordre) as total_ordres, 
                   ROUND(SUM(frais_courtage_chf), 2) as total_frais_chf,
                   ROUND(SUM(montant_brut_chf), 2) as volume_chf
            FROM table_ordres_bourse 
            GROUP BY date_ordre 
            ORDER BY date_ordre DESC 
            LIMIT 15;
            """
        else:
            sql = """
            SELECT CAST(id_ordre AS VARCHAR) as id_ordre, 
                   client_id, isin, quantite, 
                   prix_unitaire_chf, montant_brut_chf, 
                   frais_courtage_chf, date_ordre 
            FROM table_ordres_bourse 
            ORDER BY id_ordre DESC 
            LIMIT 15;
            """

        df_result = con.execute(sql).df()
        con.close()
        return sql.strip(), df_result, "CONNECTED"

    except Exception as e:
        if con:
            con.close()
        return f"-- Erreur SQL : {e}", pd.DataFrame(), "ERROR"

# =============================================================================
# 4. CONSTRUCTEUR DYNAMIQUE DE GRAPHIQUES PLOTLY POUR DONNÉES RÉELLES
# =============================================================================
def construire_visuel_plotly_reel(df: pd.DataFrame, titre: str):
    """Génère un graphique Plotly réactif adapté aux vraies données extraites."""
    if df is None or df.empty:
        return None

    cols = df.columns.tolist()

    # Case 1 : Vue détaillée par ID Ordre
    if "id_ordre" in cols and "montant_brut_chf" in cols:
        fig = px.bar(
            df,
            x="id_ordre",
            y="montant_brut_chf",
            color="client_id" if "client_id" in cols else None,
            hover_data=[c for c in ["isin", "quantite", "prix_unitaire_chf"] if c in cols],
            title=f"📊 {titre} (Vraies Données DWH)",
            labels={"id_ordre": "N° Ordre", "montant_brut_chf": "Montant Brut (CHF)", "client_id": "Client"},
            text_auto='.2s'
        )
    # Case 2 : Aggrégation par Client
    elif "client_id" in cols and "total_aum_chf" in cols:
        fig = px.bar(
            df,
            x="client_id",
            y="total_aum_chf",
            title=f"📊 Volume Total par Client (Vraies Données DWH)",
            labels={"client_id": "Client", "total_aum_chf": "Volume Total (CHF)"},
            text_auto='.2s',
            color_discrete_sequence=['#003366']
        )
    # Case 3 : Aggrégation par Date (Série temporelle)
    elif "date_ordre" in cols and "volume_chf" in cols:
        fig = px.line(
            df,
            x="date_ordre",
            y="volume_chf",
            title=f"📈 Évolution du Volume par Date (Vraies Données DWH)",
            markers=True
        )
    else:
        num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string', 'category']).columns.tolist()
        if cat_cols and num_cols:
            fig = px.bar(df, x=cat_cols[0], y=num_cols[0], title=f"📊 {titre}")
        else:
            return None

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(type='category') if "id_ordre" in cols else {}
    )
    return fig

# =============================================================================
# 5. INITIALISATION DE LA SESSION STATE
# =============================================================================
if "current_sql" not in st.session_state or "current_df" not in st.session_state:
    sql, df, status = executer_requete_duckdb_reelle("ordres")
    st.session_state.current_sql = sql
    st.session_state.current_df = df
    st.session_state.db_status = status

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bienvenue sur la version connectée en direct au Data Warehouse DuckDB !"}
    ]

# =============================================================================
# 6. BARRE LATÉRALE (SIDEBAR) AVEC INDICATEUR DUCKDB RÉEL
# =============================================================================
st.title("🏦 Geneva Wealth Analytics — Mode DuckDB Réel")
st.caption("Connexion directe à 'banque_geneve_dwh.duckdb' & Visualisation Plotly")

with st.sidebar:
    st.header("📊 Statut de la Base de Données")

    # Vérification physique de DuckDB
    con, is_connected = get_duckdb_connection(read_only=True)
    if is_connected and con:
        try:
            nb_ordres = con.execute("SELECT COUNT(*) FROM table_ordres_bourse;").fetchone()[0]
            vol_total = con.execute("SELECT COALESCE(SUM(montant_brut_chf), 0.0) FROM table_ordres_bourse;").fetchone()[0]
            con.close()

            # 🟢 BLOC EN VERT : STATUT CONNECTÉ SUR VRAIS DONNÉES
            st.success("🟢 **STATUT : CONNECTÉ AU DWH**\n\nBase DuckDB Physique Détectée")
            st.markdown("---")
            st.metric("Vrais Ordres en DWH", f"{nb_ordres:,}")
            st.metric("Volume Total DWH", f"{vol_total:,.2f} CHF")
        except Exception:
            con.close()
            st.warning("🟠 **STATUT : CONNECTÉ (BASE VIDE)**\n\nLa table 'table_ordres_bourse' n'est pas encore alimentée.")
    else:
        st.error("🔴 **STATUT : NON CONNECTÉ**\n\nFichier 'banque_geneve_dwh.duckdb' introuvable dans 'Base de donnée/'.")

    st.markdown("---")
    if st.button("🔄 Rafraîchir les Données DWH"):
        sql, df, status = executer_requete_duckdb_reelle("ordres")
        st.session_state.current_sql = sql
        st.session_state.current_df = df
        st.session_state.db_status = status
        st.rerun()

st.markdown("---")

# =============================================================================
# 7. AFFICHAGE PRINCIPAL DES VRAIES DONNÉES DWH (NIVEAU RACINE)
# =============================================================================
col_gauche, col_droite = st.columns(2)

with col_gauche:
    st.subheader(f"📄 Données DWH Réelles ({len(st.session_state.current_df)} enregistrements)")
    st.code(st.session_state.current_sql, language="sql")
    
    if not st.session_state.current_df.empty:
        st.dataframe(st.session_state.current_df, use_container_width=True, height=400)
    else:
        st.info("Aucune donnée disponible dans le Data Warehouse physique. Veuillez exécuter le pipeline d'ingestion Prefect pour alimenter DuckDB.")

with col_droite:
    st.subheader("📊 Graphique Plotly (Données Réelles)")
    if not st.session_state.current_df.empty:
        fig = construire_visuel_plotly_reel(st.session_state.current_df, "Visualisation DWH")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Structure de données non adaptée à la visualisation.")
    else:
        st.info("En attente de données réelles pour l'affichage du graphique.")

st.markdown("---")

# =============================================================================
# 8. ZONE CONVERSATIONNELLE CHATBOT
# =============================================================================
st.subheader("💬 Assistant Conversational (Text-to-SQL Réel)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Ex: Posez une question sur les données de la base..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Exécution de la vraie requête SQL basée sur la question
    sql, df_res, status = executer_requete_duckdb_reelle(user_input)
    st.session_state.current_sql = sql
    st.session_state.current_df = df_res
    st.session_state.db_status = status
    
    reponse = f"Requête SQL exécutée sur la base DuckDB réelle pour : '{user_input}'."
    st.session_state.messages.append({"role": "assistant", "content": reponse})
    
    # Rerun propre pour préserver le tableau et le visuel Plotly
    st.rerun()