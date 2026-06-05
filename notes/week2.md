# Résumé Semaine 2

## Ce qu'on a fait
- Autoencoder PyTorch entraîné (12→8→4→8→12)
- Loss finale : 0.052 après 50 epochs
- Threshold : P95 = 0.202
- Isolation Forest entraîné en 5.6 secondes

## Résultats
- Autoencoder : 5.0% anomalies, AUC-ROC = 0.96
- Isolation Forest : 1.8% anomalies, AUC-ROC = 0.86
- Corrélation entre modèles : 0.477

## Conclusion
L'Autoencoder est le meilleur modèle principal.
Isolation Forest utilisé comme validation croisée.

## Apprentissages
- Seed important pour reproductibilité
- Dataset non labelisé → métriques non supervisées
- Les deux modèles sont complémentaires