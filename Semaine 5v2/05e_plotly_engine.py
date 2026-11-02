import plotly.express as px
import pandas as pd

def generer_visuel_dynamique(df: pd.DataFrame, titre: str = "Analyse Financière DWH"):
    """
    Analyse la structure du DataFrame et génère le graphique Plotly le plus adapté.
    """
    if df is None or df.empty:
        return None

    cols = df.columns.tolist()

    # 1. Série temporelle -> Line Chart
    date_cols = [c for c in cols if 'date' in c.lower() or 'jour' in c.lower()]
    num_cols = [c for c in cols if df[c].dtype in ['float64', 'int64'] and c not in date_cols]

    if date_cols and num_cols:
        fig = px.line(
            df, x=date_cols[0], y=num_cols[0],
            title=f"📈 {titre}",
            markers=True
        )
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        return fig

    # 2. Répartition à 2 colonnes (ex: Catégorie / Montant) -> Bar Chart
    elif len(cols) == 2 and num_cols:
        cat_col = [c for c in cols if c not in num_cols][0]
        fig = px.bar(
            df, x=cat_col, y=num_cols[0],
            title=f"📊 {titre}",
            text_auto='.2f',
            color_discrete_sequence=['#003366'] # Bleu Institutionnel
        )
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        return fig

    # 3. Graphique multi-colonnes par défaut
    elif len(num_cols) >= 1:
        fig = px.bar(df, x=cols[0], y=num_cols[0], title=f"📊 {titre}")
        fig.update_layout(template="plotly_white")
        return fig

    return None

if __name__ == '__main__':
    df_sample = pd.DataFrame({
        "segment_client": ["UHNWI", "HNWI", "Retail"],
        "total_aum_chf": [2500000.0, 850000.0, 150000.0]
    })
    fig = generer_visuel_dynamique(df_sample, "AuM par Segment Client")
    print("✅ Visuel Plotly initialisé avec succès.")