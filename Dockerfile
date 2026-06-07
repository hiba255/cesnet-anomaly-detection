# Image Python de base légère
FROM python:3.10-slim

# Définir le dossier de travail
WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Exposer le port 8000
EXPOSE 8000

# Lancer l'API au démarrage
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]