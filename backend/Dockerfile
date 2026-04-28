# Utilisation de la version stable officielle
FROM python:3.12-slim

# On installe le client Docker au cas où le worker en a besoin en interne
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

# On définit le dossier de travail dans le conteneur
WORKDIR /app

# On copie d'abord les dépendances (pour optimiser le cache Docker)
COPY requirements.txt .

# On installe tout (Pas besoin de venv, le conteneur EST la bulle)
RUN pip install --no-cache-dir -r requirements.txt

# On copie le reste de ton code
COPY . .