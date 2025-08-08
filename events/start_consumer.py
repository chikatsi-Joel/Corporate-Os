#!/usr/bin/env python3
"""
Script de démarrage du consumer d'événements RabbitMQ
"""

import sys
import os
import logging
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from events.consumer import start_consumer
from core.event_type import EventTypeEnum

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fonction principale"""
    logger.info("🚀 Démarrage du consumer d'événements...")
    
    try:
        # Afficher les types d'événements supportés
        logger.info("📋 Types d'événements supportés:")
        for event_type in EventTypeEnum:
            logger.info(f"  - {event_type.value}")
        
        # Attendre que RabbitMQ soit prêt
        logger.info("⏳ Attente que RabbitMQ soit prêt...")
        time.sleep(10)
        
        # Démarrer le consumer
        logger.info("📡 Démarrage de la consommation d'événements...")
        logger.info("📊 Handlers disponibles:")
        logger.info("  - AuditEventHandler: Gestion des événements d'audit")
        logger.info("  - NotificationEventHandler: Gestion des notifications")
        logger.info("  - SystemEventHandler: Gestion des événements système")
        
        start_consumer('events')
        
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage du consumer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


