from fastapi import FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import sys
from pathlib import Path
import json
import io

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