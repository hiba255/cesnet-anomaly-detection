import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from io import StringIO

# Configuration de la page
st.set_page_config(
    page_title="Détection d'Anomalies Réseau",
    page_icon="🛡️",
    layout="wide"
)

# Titre principal
st.title("🛡️ Système de Détection d'Anomalies Réseau")
st.markdown("**Dataset CESNET-TimeSeries24 | Autoencoder PyTorch | Non Supervisé**")
st.divider()

# Sidebar
st.sidebar.title("⚙️ Configuration")
api_url = st.sidebar.text_input("URL de l'API", value="http://localhost:8000")

# Vérifier l'état de l'API
try:
    response = requests.get(f"{api_url}/health", timeout=3)
    if response.status_code == 200:
        health = response.json()
        st.sidebar.success("✅ API connectée")
        st.sidebar.info(f"Threshold : {health['threshold']:.4f}")
    else:
        st.sidebar.error("❌ API non disponible")
except:
    st.sidebar.error("❌ API non disponible")

st.sidebar.divider()

# Upload fichier
st.sidebar.title("📁 Upload CSV")
uploaded_file = st.sidebar.file_uploader(
    "Glisse ton fichier CSV ici",
    type=['csv'],
    help="Format CESNET : 12 features réseau"
)

# Filtre
st.sidebar.title("🔍 Filtres")
show_filter = st.sidebar.selectbox(
    "Afficher",
    ["Tout", "Anomalies uniquement", "Normal uniquement"]
)
# Zone principale
if uploaded_file is not None:
    # Lire le fichier
    df_input = pd.read_csv(uploaded_file)
    
    st.subheader(f"📊 Fichier chargé : {uploaded_file.name} ({len(df_input)} connexions)")
    
    # Envoyer à l'API
    with st.spinner("🔍 Analyse en cours..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = requests.post(f"{api_url}/predict", files=files, timeout=60)
            result = response.json()
        except Exception as e:
            st.error(f"Erreur API : {e}")
            st.stop()
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Connexions", result['total_connections'])
    col2.metric("🚨 Anomalies", result['anomalies_detected'], 
                delta=f"{result['anomaly_rate']:.1f}%", delta_color="inverse")
    col3.metric("✅ Normal", result['normal_connections'])
    col4.metric("Threshold", f"{result['threshold']:.4f}")
    
    st.divider()
    
    # Graphiques
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Camembert
        fig_pie = px.pie(
            values=[result['normal_connections'], result['anomalies_detected']],
            names=['Normal', 'Anomalie'],
            color_discrete_map={'Normal': '#2ECC71', 'Anomalie': '#E74C3C'},
            title="Distribution Normal vs Anomalie"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_right:
        # Erreurs de reconstruction
        errors = [r['error'] for r in result['results']]
        labels = [r['label'] for r in result['results']]
        colors = ['#E74C3C' if l == 'anomalie' else '#2ECC71' for l in labels]
        
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            y=errors,
            mode='markers',
            marker=dict(color=colors, size=8),
            name='Erreur de reconstruction'
        ))
        fig_scatter.add_hline(
            y=result['threshold'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"Seuil = {result['threshold']:.4f}"
        )
        fig_scatter.update_layout(title="Erreurs de Reconstruction par Connexion")
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.divider()
    
    # Tableau des résultats
    df_results = pd.DataFrame(result['results'])
    df_results['status'] = df_results['label'].apply(
        lambda x: '🚨 ANOMALIE' if x == 'anomalie' else '✅ Normal'
    )
    
    # Appliquer le filtre
    if show_filter == "Anomalies uniquement":
        df_results = df_results[df_results['label'] == 'anomalie']
    elif show_filter == "Normal uniquement":
        df_results = df_results[df_results['label'] == 'normal']
    
    st.subheader(f"📋 Résultats détaillés ({len(df_results)} connexions)")
    st.dataframe(
        df_results[['row', 'status', 'error']].rename(columns={
            'row': 'Connexion',
            'status': 'Statut',
            'error': 'Erreur MSE'
        }),
        use_container_width=True
    )
    
    # Bouton téléchargement
    csv_download = df_results.to_csv(index=False)
    st.download_button(
        label="⬇️ Télécharger les résultats CSV",
        data=csv_download,
        file_name="resultats_anomalies.csv",
        mime="text/csv"
    )

else:
    # Page d'accueil
    st.info("👈 Upload un fichier CSV dans la sidebar pour commencer l'analyse !")
    
    col1, col2, col3 = st.columns(3)
    col1.markdown("### 🧠 Modèle\nAutoencoder PyTorch\n12→8→4→8→12")
    col2.markdown("### 📊 Dataset\nCESNET-TimeSeries24\n952 697 connexions")
    col3.markdown("### 🎯 Performance\nAUC-ROC : 0.96\nThreshold : P95")