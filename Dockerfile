FROM python:3.11-alpine

# Métadonnées
LABEL maintainer="Docker Swarm Prometheus Exporter"
LABEL description="Exporteur de métriques Docker Swarm pour Prometheus"
LABEL version="1.0.0"

# Variables d'environnement par défaut
ENV EXPORTER_PORT=8080
ENV EXPORTER_INTERVAL=30
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers

# Création d'un utilisateur non-root pour la sécurité
RUN addgroup -g 1001 -S exporter && \
    adduser -u 1001 -S exporter -G exporter

# Répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du script principal
COPY exporter.py .

# Changement vers l'utilisateur non-root
USER exporter

# Exposition du port
EXPOSE ${EXPORTER_PORT}

# Health check pour vérifier que l'exporteur fonctionne
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${EXPORTER_PORT}/metrics || exit 1

# Point d'entrée
CMD ["python", "exporter.py"]