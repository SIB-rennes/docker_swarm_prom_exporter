#!/usr/bin/env python3
"""
Docker Swarm Prometheus Exporter

Ce script expose les métriques des services Docker Swarm au format Prometheus.
Il collecte les informations sur le statut des services et leur dernière mise à jour.
"""

import time
import logging
import docker
from prometheus_client import Gauge, start_http_server
from prometheus_client.core import CollectorRegistry

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerSwarmExporter:
    """Exporteur de métriques Docker Swarm pour Prometheus"""
    
    def __init__(self, port: int = 8080, interval: int = 30):
        """
        Initialise l'exporteur
        
        Args:
            port: Port d'écoute pour les métriques
            interval: Intervalle de mise à jour en secondes
        """
        self.port = port
        self.interval = interval
        self.registry = CollectorRegistry()
        
        # Initialisation du client Docker
        try:
            self.client = docker.from_env()
            # Test de connexion au daemon Docker Swarm
            self.client.swarm.attrs
            logger.info("Connexion réussie au daemon Docker Swarm")
        except docker.errors.APIError as e:
            logger.error(f"Erreur lors de la connexion à Docker Swarm: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            raise
        
        # Définition des métriques Prometheus
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Configure les métriques Prometheus"""
        
        # Métriques pour les mises à jour uniquement
        self.service_update_status = Gauge(
            'docker_swarm_service_update_status',
            'Statut de la dernière mise à jour (1=completed, 0.5=updating, 0=failed)',
            ['service_name', 'service_id', 'update_state'],
            registry=self.registry
        )
    

    
    def _get_update_status_value(self, update_status: str) -> float:
        """
        Convertit le statut de mise à jour en valeur numérique
        
        Args:
            update_status: Statut de mise à jour ('completed', 'updating', 'paused', 'failed', etc.)
            
        Returns:
            1.0 pour completed
            0.5 pour updating
            0.0 pour paused, failed ou autre
        """
        status_map = {
            'completed': 1.0,
            'updating': 0.5,
            'paused': 0.0,
            'failed': 0.0,
            'rollback_completed': 1.0,
            'rollback_paused': 0.0,
            'rollback_started': 0.5
        }
        return status_map.get(update_status.lower(), 0.0)
    

    
    def collect_metrics(self):
        """Collecte les métriques des services Docker Swarm"""
        try:
            logger.info("Collecte des métriques Docker Swarm...")
            
            # Collecte des informations sur les services
            services = self.client.services.list()
            logger.info(f"Trouvé {len(services)} services")
            
            for service in services:
                service_name = service.name
                service_id = service.id[:12]  # Prendre seulement les 12 premiers caractères
                
                try:
                    # Statut de mise à jour uniquement
                    update_status = service.attrs.get('UpdateStatus', {})
                    if update_status:
                        state = update_status.get('State', 'unknown')
                        update_value = self._get_update_status_value(state)
                        
                        self.service_update_status.labels(
                            service_name=service_name,
                            service_id=service_id,
                            update_state=state
                        ).set(update_value)
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du service {service_name}: {e}")
                    continue
            
            logger.info("Collecte des métriques terminée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques: {e}")
    
    def run(self):
        """Lance l'exporteur de métriques"""
        logger.info(f"Démarrage de l'exporteur sur le port {self.port}")
        
        # Démarrage du serveur HTTP Prometheus
        start_http_server(self.port, registry=self.registry)
        logger.info(f"Serveur de métriques démarré sur http://0.0.0.0:{self.port}/metrics")
        
        # Boucle principale de collecte
        while True:
            try:
                self.collect_metrics()
                logger.debug(f"Attente de {self.interval} secondes avant la prochaine collecte")
                time.sleep(self.interval)
            except KeyboardInterrupt:
                logger.info("Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle principale: {e}")
                logger.info(f"Nouvelle tentative dans {self.interval} secondes")
                time.sleep(self.interval)

def main():
    """Point d'entrée principal"""
    import os
    
    # Configuration depuis les variables d'environnement
    port = int(os.getenv('EXPORTER_PORT', '8080'))
    interval = int(os.getenv('EXPORTER_INTERVAL', '30'))
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configuration du niveau de log
    numeric_level = getattr(logging, log_level, logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    
    logger.info(f"Configuration: port={port}, interval={interval}s, log_level={log_level}")
    
    # Création et lancement de l'exporteur
    exporter = DockerSwarmExporter(port=port, interval=interval)
    exporter.run()

if __name__ == '__main__':
    main()