from sklearn.datasets import fetch_kddcup99
import pandas as pd

print("Téléchargement KDD Cup 99...")
data = fetch_kddcup99(subset='SA', percent10=True, as_frame=True)
df = data.frame
df.to_csv('data/kdd_cup99.csv', index=False)
print(f"Dataset téléchargé : {df.shape}")
print(f"Labels :\n{df['labels'].value_counts().head()}")