import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path

# Chemin vers les modèles
MODELS_PATH = Path(__file__).parent.parent / 'models'

# Architecture Autoencoder (identique au notebook)
class Autoencoder(nn.Module):
    def __init__(self, input_dim=12):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(12, 8), nn.ReLU(),
            nn.Linear(8, 4), nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8), nn.ReLU(),
            nn.Linear(8, 12)
        )
    def forward(self, x):
        return self.decoder(self.encoder(x))

# Charger modèle + config
def load_model():
    with open(MODELS_PATH / 'config.json', 'r') as f:
        config = json.load(f)
    
    model = Autoencoder()
    model.load_state_dict(torch.load(MODELS_PATH / 'autoencoder.pth', 
                                      map_location='cpu'))
    model.eval()
    
    scaler = joblib.load(MODELS_PATH / 'scaler.pkl')
    return model, scaler, config

# Fonction principale de prédiction
def predict(df: pd.DataFrame):
    model, scaler, config = load_model()
    
    features = config['features']
    skewed = config['skewed_features']
    threshold = config['threshold']
    
    # Vérifier les colonnes
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")
    
    # Prétraitement
    df_proc = df[features].copy().astype(float)
    for col in skewed:
        if col in df_proc.columns:
            df_proc[col] = np.log1p(df_proc[col])
    
    # Normalisation
    X = scaler.transform(df_proc.values)
    X_tensor = torch.FloatTensor(X)
    
    # Prédiction
    with torch.no_grad():
        X_pred = model(X_tensor)
        errors = torch.mean((X_tensor - X_pred) ** 2, dim=1).numpy()
    
    # Résultats
    labels = (errors > threshold).astype(int)
    
    return {
        'labels': labels,           # 0 = normal, 1 = anomalie
        'errors': errors,           # erreur de reconstruction
        'threshold': threshold,
        'n_anomalies': int(labels.sum()),
        'n_normal': int((labels == 0).sum()),
        'anomaly_rate': float(labels.mean() * 100)
    }