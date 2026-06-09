import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import time
import websocket
import threading
from collections import deque
import datetime

# Configuration
st.set_page_config(
    page_title="Détection d'Anomalies Réseau — Temps Réel",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Détection d'Anomalies Réseau — Temps Réel")
st.markdown("**CESNET-TimeSeries24 | Autoencoder PyTorch | Live Dashboard**")
st.divider()

# Sidebar
st.sidebar.title("⚙️ Configuration")
api_url = st.sidebar.text_input("URL API", value="http://localhost:8000")
ws_url = st.sidebar.text_input("URL WebSocket", value="ws://localhost:8000/ws/realtime")

# Vérifier API
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
st.sidebar.title("📁 Test Manuel")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])

# Métriques temps réel
col1, col2, col3, col4 = st.columns(4)
total_placeholder = col1.empty()
anomaly_placeholder = col2.empty()
normal_placeholder = col3.empty()
rate_placeholder = col4.empty()

st.divider()

# Graphiques
col_left, col_right = st.columns(2)
with col_left:
    chart_placeholder = st.empty()
with col_right:
    scatter_placeholder = st.empty()

st.divider()

# Tableau temps réel
st.subheader("📋 Flux réseau en temps réel")
table_placeholder = st.empty()

# État session
if 'results' not in st.session_state:
    st.session_state.results = []
if 'total' not in st.session_state:
    st.session_state.total = 0
if 'anomalies' not in st.session_state:
    st.session_state.anomalies = 0

def update_display():
    results = st.session_state.results[-50:]  # 50 derniers
    total = st.session_state.total
    anomalies = st.session_state.anomalies
    normal = total - anomalies
    rate = (anomalies / total * 100) if total > 0 else 0

    # Métriques
    total_placeholder.metric("Total Flows", total)
    anomaly_placeholder.metric("🚨 Anomalies", anomalies, delta=f"{rate:.1f}%", delta_color="inverse")
    normal_placeholder.metric("✅ Normal", normal)
    rate_placeholder.metric("Taux Anomalies", f"{rate:.1f}%")

    if results:
        df_results = pd.DataFrame(results)

        # Camembert
        fig_pie = px.pie(
            values=[normal, anomalies],
            names=['Normal', 'Anomalie'],
            color_discrete_map={'Normal': '#2ECC71', 'Anomalie': '#E74C3C'},
            title="Distribution en temps réel"
        )
        chart_placeholder.plotly_chart(fig_pie, use_container_width=True)

        # Scatter erreurs
        fig_scatter = go.Figure()
        colors = ['#E74C3C' if r['label'] == 'anomalie' else '#2ECC71' for r in results]
        fig_scatter.add_trace(go.Scatter(
            y=[r['error'] for r in results],
            mode='lines+markers',
            marker=dict(color=colors, size=8),
            line=dict(color='steelblue', width=1),
            name='Erreur MSE'
        ))
        fig_scatter.add_hline(
            y=results[0]['threshold'] if results else 0.149,
            line_dash="dash",
            line_color="red",
            annotation_text="Seuil"
        )
        fig_scatter.update_layout(title="Erreurs de Reconstruction Live")
        scatter_placeholder.plotly_chart(fig_scatter, use_container_width=True)

        # Tableau
        df_display = pd.DataFrame(results[-20:])
        df_display['status'] = df_display['label'].apply(
            lambda x: '🚨 ANOMALIE' if x == 'anomalie' else '✅ Normal'
        )
        df_display['time'] = pd.to_datetime(df_display['timestamp'], unit='s').dt.strftime('%H:%M:%S')
        table_placeholder.dataframe(
            df_display[['time', 'status', 'error']].rename(columns={
                'time': 'Heure',
                'status': 'Statut',
                'error': 'Erreur MSE'
            }),
            use_container_width=True
        )

# Mode temps réel
st.sidebar.divider()
realtime_mode = st.sidebar.toggle("🔴 Mode Temps Réel", value=False)

if realtime_mode:
    st.sidebar.success("🔴 LIVE")
    
    try:
        ws = websocket.create_connection(ws_url, timeout=30)
        st.info("🔴 Connexion WebSocket établie — En attente de trafic réseau...")
        
        while realtime_mode:
            try:
                result = json.loads(ws.recv())
                st.session_state.results.append(result)
                st.session_state.total += 1
                if result['is_anomaly']:
                    st.session_state.anomalies += 1
                
                update_display()
                time.sleep(0.1)
                
            except Exception as e:
                st.warning(f"En attente de données... ({e})")
                time.sleep(1)
                
    except Exception as e:
        st.error(f"Impossible de se connecter au WebSocket : {e}")

elif uploaded_file is not None:
    # Mode manuel
    df_input = pd.read_csv(uploaded_file)
    with st.spinner("Analyse en cours..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = requests.post(f"{api_url}/predict", files=files, timeout=60)
            result = response.json()
            
            for r in result['results']:
                r['timestamp'] = time.time()
                r['is_anomaly'] = r['label'] == 'anomalie'
                st.session_state.results.append(r)
                st.session_state.total += 1
                if r['is_anomaly']:
                    st.session_state.anomalies += 1
            
            update_display()
            
        except Exception as e:
            st.error(f"Erreur : {e}")
else:
    st.info("👈 Active le Mode Temps Réel ou upload un CSV pour commencer !")
    col1, col2, col3 = st.columns(3)
    col1.markdown("### 🧠 Modèle\nAutoencoder PyTorch\n12→8→4→8→12")
    col2.markdown("### 📊 Dataset\nCESNET-TimeSeries24\n952 697 connexions")
    col3.markdown("### 🎯 Performance\nAUC-ROC : 0.96\nThreshold : P95")