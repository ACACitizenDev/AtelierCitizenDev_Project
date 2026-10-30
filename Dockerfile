# -----------------------------------------------------------------------------
# IMAGE DE BASE : Python 3.15 Slim (Linux Debian minimaliste)
# -----------------------------------------------------------------------------
FROM python:3.15-slim

# Éviter l'écriture de fichiers .pyc et forcer l'affichage immédiat des logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Définition du répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Installation des paquets système nécessaires pour la compilation minimale
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'intégralité du projet dans le conteneur
COPY . /app/

# Commande par défaut au démarrage du conteneur
CMD ["python", "Semaine 5/07_orchestrator_prefect.py"]