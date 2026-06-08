# Résumé Semaine 3

## Ce qu'on a fait

### FastAPI
- Créé api/main.py avec 4 endpoints :
  - GET / → statut de l'API
  - GET /health → santé du modèle
  - GET /model-info → infos architecture
  - POST /predict → analyse un fichier CSV
- Documentation Swagger automatique sur /docs
- Testé avec test_sample.csv → 100 connexions, 0 anomalies

### Docker
- Créé Dockerfile (image python:3.10-slim)
- Créé docker-compose.yml
- Créé requirements.txt
- Image buildée : cesnet-api
- API tourne dans Docker sur http://localhost:8000
- Commande de lancement : docker-compose up

## Apprentissages
- FastAPI génère automatiquement la doc Swagger
- Docker permet de déployer l'app en une seule commande
- WSL2 nécessaire pour Docker Desktop sur Windows
- Le volume ./models monte les modèles dans le container

## Commandes clés
- Lancer l'API locale : uvicorn api.main:app --reload
- Lancer Docker : docker-compose up
- Arrêter Docker : docker-compose down
- Rebuilder : docker-compose build