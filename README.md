# Docker Swarm Prometheus Exporter

Exporteur de métriques pour Docker Swarm qui expose le statut des mises à jour des services au format Prometheus.

## 🎯 Fonctionnalités

- **Statut des mises à jour** : Monitoring du statut des déploiements et rollbacks des services Docker Swarm

## 📊 Métriques exposées

### docker_swarm_service_update_status

**Type :** Gauge  
**Description :** Statut de la dernière mise à jour du service  
**Labels :**
- `service_name` : Nom du service Docker Swarm
- `service_id` : ID court du service (12 premiers caractères)
- `update_state` : État de la mise à jour

**Valeurs :**
- `1.0` : Mise à jour terminée avec succès (`completed`, `rollback_completed`)
- `0.5` : Mise à jour en cours (`updating`, `rollback_started`)
- `0.0` : Mise à jour en pause ou échouée (`paused`, `failed`, `rollback_paused`)

**Exemple de sortie :**
```prometheus
# HELP docker_swarm_service_update_status Statut de la dernière mise à jour (1=completed, 0.5=updating, 0=failed)
# TYPE docker_swarm_service_update_status gauge
docker_swarm_service_update_status{service_name="web-app",service_id="abc123def456",update_state="completed"} 1.0
docker_swarm_service_update_status{service_name="api-service",service_id="def456ghi789",update_state="updating"} 0.5
docker_swarm_service_update_status{service_name="worker",service_id="ghi789jkl012",update_state="failed"} 0.0
```

## 🚀 Construction et déploiement

### 1. Construire l'image

```bash
docker build -t docker-swarm-prometheus-exporter .
```

### 2. Lancement simple

```bash
docker run -d \
  --name swarm-exporter \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  docker-swarm-prometheus-exporter
```

### 3. Déploiement Swarm

```bash
docker service create \
  --name swarm-exporter \
  --mode global \
  --constraint 'node.role==manager' \
  --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,readonly \
  --publish 8080:8080 \
  docker-swarm-prometheus-exporter
```

### 4. Avec Docker Compose

```bash
docker stack deploy -c docker-compose.yml swarm-monitoring
```

## ⚙️ Configuration

Variables d'environnement disponibles :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `EXPORTER_PORT` | `8080` | Port d'écoute |
| `EXPORTER_INTERVAL` | `30` | Intervalle de collecte (secondes) |
| `LOG_LEVEL` | `INFO` | Niveau de log |

## 📈 Utilisation

Les métriques sont disponibles sur `http://localhost:8080/metrics`

Exemple de configuration Prometheus :
```yaml
scrape_configs:
  - job_name: 'docker-swarm'
    static_configs:
      - targets: ['localhost:8080']
```

## 🛡️ Sécurité

- L'image utilise un utilisateur non-root
- Le socket Docker est monté en lecture seule
- Déploiement recommandé sur les nœuds manager uniquement

## 📦 Images précompilées

Les images Docker sont automatiquement publiées sur GitHub Container Registry :

```bash
# Dernière version stable
docker pull ghcr.io/OWNER/REPO:latest

# Version spécifique
docker pull ghcr.io/OWNER/REPO:v1.0.0
```

> **Note :** Remplacez `OWNER/REPO` par le nom de votre dépôt GitHub

## 🚀 Publication automatique

### Workflow GitHub Actions

Le projet inclut un workflow GitHub Actions qui :

1. **Se déclenche automatiquement** lors d'un push de tag (format `v*.*.*`)
2. **Compile pour multiple architectures** (amd64, arm64) 
3. **Publie sur ghcr.io** avec authentification automatique
4. **Génère plusieurs tags** :
   - `v1.2.3` (tag exact)
   - `v1.2` (version majeure.mineure)
   - `v1` (version majeure)
   - `latest` (dernière version)

### Créer une release

```bash
# Créer et pousser un tag
git tag v1.0.0
git push origin v1.0.0

# L'image sera automatiquement disponible sur :
# ghcr.io/OWNER/REPO:v1.0.0
# ghcr.io/OWNER/REPO:v1.0
# ghcr.io/OWNER/REPO:v1
# ghcr.io/OWNER/REPO:latest
```