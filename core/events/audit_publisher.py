import pika
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable
from pika.exchange_type import ExchangeType
import logging

logger = logging.getLogger(__name__)


class AuditPublisher:
    """Publisher pour envoyer des notifications"""
    
    def __init__(self, rabbitmq_url: str = None):
        try:
            # Utiliser la configuration par défaut si aucune URL n'est fournie
            if rabbitmq_url is None:
                from app.core.config import settings
                rabbitmq_url = settings.rabbitmq_url
            
            logger.info(f"Tentative de connexion à RabbitMQ: {rabbitmq_url}")
            self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(exchange='audit', exchange_type=ExchangeType.fanout)
            logger.info("Connexion RabbitMQ établie avec succès")
        except Exception as e:
            logger.warning(f"Impossible de se connecter à RabbitMQ: {e}")
            self.connection = None
            self.channel = None
    
    def publish_for_audit(self, message: str, notification_type: str = 'info', metadata: Dict[str, Any] = None):
        """Publier pour l'audit"""
        if self.connection is None or self.channel is None:
            logger.warning("RabbitMQ non disponible, message d'audit ignoré")
            return
        
        try:
            notification = {
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            self.channel.basic_publish(
                exchange='audit',
                routing_key='',  # Ignoré pour fanout exchange
                body=json.dumps(notification),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Rendre le message persistant
                    content_type='application/json'
                )
            )
            
            logger.info(f"Notification d'audit envoyée: {message}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification d'audit: {e}")
    
    def close(self):
        """Fermer la connexion"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Connexion RabbitMQ fermée")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la connexion RabbitMQ: {e}")

