import pandas as pd
import sys
sys.path.append('.')
from utils.predictor import predict

df = pd.read_csv('data/capture_attack_cesnet.csv')
print('Données converties :')
print(df)
print()

result = predict(df)
print(f'Total connexions  : {len(df)}')
print(f'Anomalies         : {result["n_anomalies"]}')
print(f'Normal            : {result["n_normal"]}')
print(f'Taux anomalies    : {result["anomaly_rate"]:.1f}%')
print()
for i, (label, error) in enumerate(zip(result["labels"], result["errors"])):
    status = "ANOMALIE" if label == 1 else "Normal"
    print(f'IP {i+1} : {status} (erreur={error:.6f})')