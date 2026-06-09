from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import redis as redis_client
import json
import torch
import torch.nn as nn
import joblib
import numpy as np
from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import sys
from pathlib import Path
import json
import io
import os

# Connexion Redis

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_conn = redis_client.Redis(host=redis_host, port=6379, decode_responses=True)
# Autoencoder (même architecture)
class Autoencoder(nn.Module):
    def __init__(self):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(nn.Linear(12, 8), nn.ReLU(), nn.Linear(8, 4), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 12))
    def forward(self, x):
        return self.decoder(self.encoder(x))

# Charger modèle au démarrage
autoencoder = Autoencoder()
autoencoder.load_state_dict(torch.load('models/autoencoder.pth', map_location='cpu'))
autoencoder.eval()
scaler_rt = joblib.load('models/scaler.pkl')

with open('models/config.json', 'r') as f:
    config_rt = json.load(f)
threshold_rt = config_rt['threshold']
features_rt = config_rt['features']
skewed_rt = config_rt['skewed_features']
sys.path.append(str(Path(__file__).parent.parent))
from utils.predictor import predict

# Créer l'application FastAPI
app = FastAPI(
    title="API Détection d'Anomalies Réseau",
    description="Système de détection d'anomalies basé sur Autoencoder PyTorch — Dataset CESNET",
    version="1.0.0"
)

# Endpoint de base
@app.get("/")
def root():
    return {
        "message": "API Détection d'Anomalies Réseau opérationnelle",
        "version": "1.0.0",
        "status": "running"
    }
import json
from pathlib import Path

# Charger la config au démarrage
config_path = Path("models/config.json")
with open(config_path, 'r') as f:
    config = json.load(f)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "Autoencoder PyTorch",
        "threshold": config['threshold'],
        "input_features": len(config['features'])
    }

@app.get("/model-info")
def model_info():
    return {
        "model_type": "Autoencoder",
        "architecture": "12 → 8 → 4 → 8 → 12",
        "dataset": "CESNET-TimeSeries24",
        "threshold": config['threshold'],
        "features": config['features'],
        "n_features": len(config['features'])
    }
@app.post("/predict")
async def predict_anomalies(file: UploadFile = File(...)):
    # Vérifier que c'est un CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")
    
    try:
        # Lire le fichier
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Vérifier que le fichier n'est pas vide
        if df.empty:
            raise HTTPException(status_code=400, detail="Le fichier CSV est vide")
        
        # Prédiction
        result = predict(df)
        
        return {
            "filename": file.filename,
            "total_connections": len(df),
            "anomalies_detected": result['n_anomalies'],
            "normal_connections": result['n_normal'],
            "anomaly_rate": round(result['anomaly_rate'], 2),
            "threshold": result['threshold'],
            "results": [
                {
                    "row": i + 1,
                    "label": "anomalie" if result['labels'][i] == 1 else "normal",
                    "error": round(float(result['errors'][i]), 6)
                }
                for i in range(len(result['labels']))
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connecté !")
    
    try:
        while True:
            # Lire les flows depuis Redis
            flow_data = redis_conn.rpop('network_flows')
            
            if flow_data:
                data = json.loads(flow_data)
                
                # Prétraitement
                import pandas as pd
                df = pd.DataFrame([data])
                
                # Garder seulement les features
                available = [f for f in features_rt if f in df.columns]
                if len(available) == 12:
                    df_proc = df[features_rt].copy().astype(float)
                    for col in skewed_rt:
                        if col in df_proc.columns:
                            df_proc[col] = np.log1p(df_proc[col])
                    
                    X = scaler_rt.transform(df_proc.values)
                    X_tensor = torch.FloatTensor(X)
                    
                    with torch.no_grad():
                        X_pred = autoencoder(X_tensor)
                        error = torch.mean((X_tensor - X_pred) ** 2).item()
                    
                    label = "anomalie" if error > threshold_rt else "normal"
                    
                    # Envoyer résultat via WebSocket
                    result = {
                        "timestamp": data.get('timestamp', 0),
                        "label": label,
                        "error": round(error, 6),
                        "threshold": threshold_rt,
                        "is_anomaly": label == "anomalie"
                    }
                    
                    await websocket.send_json(result)
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        print("WebSocket déconnecté")