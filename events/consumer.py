"""
Consumer d'événements pour RabbitMQ
Gère la réception et le traitement des événements depuis RabbitMQ avec des handlers spécialisés
"""

import pika
import json
import logging
import threading
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from core.event_type import EventTypeEnum

logger = logging.getLogger(__name__)


class BaseEventHandler(ABC):
    """Classe de base pour les handlers d'événements"""
    
    @abstractmethod
    def handle(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Méthode abstraite pour traiter un événement"""
        pass


class AuditEventHandler(BaseEventHandler):
    """Handler spécialisé pour les événements d'audit"""
    
    def handle_user_login(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de connexion utilisateur"""
        try:
            user_id = payload.get('user_id')
            user_email = payload.get('user_email')
            user_role = payload.get('user_role')
            ip_address = payload.get('ip_address')
            
            logger.info(f"Utilisateur connecté: {user_email} ({user_role}) depuis {ip_address}")
            
            # Ici vous pouvez ajouter la logique spécifique
            # Par exemple, mettre à jour les statistiques de connexion
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la connexion: {e}")
            return False
    
    def handle_user_logout(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de déconnexion utilisateur"""
        try:
            user_id = payload.get('user_id')
            user_email = payload.get('user_email')
            session_duration = payload.get('session_duration')
            
            logger.info(f"Utilisateur déconnecté: {user_email} (session: {session_duration}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la déconnexion: {e}")
            return False
    
    def handle_shareholder_created(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de création d'actionnaire"""
        try:
            user_id = payload.get('user_id')
            shareholder_data = payload.get('shareholder_data', {})
            
            logger.info(f"Nouvel actionnaire créé par {user_id}: {shareholder_data.get('username')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la création d'actionnaire: {e}")
            return False
    
    def handle_shareholder_updated(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de mise à jour d'actionnaire"""
        try:
            user_id = payload.get('user_id')
            shareholder_id = payload.get('shareholder_id')
            previous_data = payload.get('previous_data', {})
            new_data = payload.get('new_data', {})
            
            logger.info(f"Actionnaire {shareholder_id} mis à jour par {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la mise à jour d'actionnaire: {e}")
            return False
    
    def handle_share_issued(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement d'émission d'actions"""
        try:
            user_id = payload.get('user_id')
            shareholder_id = payload.get('shareholder_id')
            share_data = payload.get('share_data', {})
            
            logger.info(f"Actions émises par {user_id} pour l'actionnaire {shareholder_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'émission d'actions: {e}")
            return False
    
    def handle_certificate_generated(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de génération de certificat"""
        try:
            user_id = payload.get('user_id')
            shareholder_id = payload.get('shareholder_id')
            certificate_path = payload.get('certificate_path')
            
            logger.info(f"Certificat généré par {user_id} pour l'actionnaire {shareholder_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la génération de certificat: {e}")
            return False
    
    def handle_permission_changed(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de changement de permission"""
        try:
            admin_user_id = payload.get('admin_user_id')
            target_user_id = payload.get('target_user_id')
            old_role = payload.get('old_role')
            new_role = payload.get('new_role')
            
            logger.info(f"Permission changée par {admin_user_id}: {target_user_id} {old_role} -> {new_role}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du changement de permission: {e}")
            return False
    
    def handle_data_export(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement d'export de données"""
        try:
            user_id = payload.get('user_id')
            export_type = payload.get('export_type')
            export_format = payload.get('export_format')
            record_count = payload.get('record_count')
            
            logger.info(f"Export de données par {user_id}: {export_type} ({record_count} enregistrements)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'export de données: {e}")
            return False
    
    def handle_system_error(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement d'erreur système"""
        try:
            error_type = payload.get('error_type')
            error_message = payload.get('error_message')
            stack_trace = payload.get('stack_trace')
            
            logger.error(f"Erreur système détectée: {error_type} - {error_message}")
            
            # Ici vous pouvez ajouter la logique d'alerte
            # Par exemple, envoyer une notification aux administrateurs
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'erreur système: {e}")
            return False
    
    def handle(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Méthode générique pour traiter un événement d'audit"""
        event_type = payload.get('event_type')
        
        if event_type == EventTypeEnum.USER_LOGIN.value:
            return self.handle_user_login(payload, event_id)
        elif event_type == EventTypeEnum.USER_LOGOUT.value:
            return self.handle_user_logout(payload, event_id)
        elif event_type == EventTypeEnum.SHAREHOLDER_CREATED.value:
            return self.handle_shareholder_created(payload, event_id)
        elif event_type == EventTypeEnum.SHAREHOLDER_UPDATED.value:
            return self.handle_shareholder_updated(payload, event_id)
        elif event_type == EventTypeEnum.SHARE_ISSUED.value:
            return self.handle_share_issued(payload, event_id)
        elif event_type == EventTypeEnum.CERTIFICATE_GENERATED.value:
            return self.handle_certificate_generated(payload, event_id)
        elif event_type == EventTypeEnum.PERMISSION_CHANGED.value:
            return self.handle_permission_changed(payload, event_id)
        elif event_type == EventTypeEnum.DATA_EXPORT.value:
            return self.handle_data_export(payload, event_id)
        elif event_type == EventTypeEnum.SYSTEM_ERROR.value:
            return self.handle_system_error(payload, event_id)
        else:
            logger.warning(f"Type d'événement d'audit non reconnu: {event_type}")
            return False


class NotificationEventHandler(BaseEventHandler):
    """Handler spécialisé pour les événements de notification"""
    
    def handle_share_issuance_notification(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite une notification d'émission d'actions"""
        try:
            user_id = payload.get('user_id')
            notification_type = payload.get('notification_type')
            title = payload.get('title')
            message = payload.get('message')
            metadata = payload.get('metadata', {})
            
            logger.info(f"Notification d'émission d'actions envoyée à {user_id}: {title}")
            
            # Ici vous pouvez ajouter la logique d'envoi de notification
            # Par exemple, envoyer un email, une notification push, etc.
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la notification d'émission: {e}")
            return False
    
    def handle_certificate_notification(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite une notification de certificat généré"""
        try:
            user_id = payload.get('user_id')
            notification_type = payload.get('notification_type')
            title = payload.get('title')
            message = payload.get('message')
            metadata = payload.get('metadata', {})
            
            logger.info(f"Notification de certificat envoyée à {user_id}: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la notification de certificat: {e}")
            return False
    
    def handle_system_alert(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite une alerte système"""
        try:
            user_id = payload.get('user_id')
            notification_type = payload.get('notification_type')
            title = payload.get('title')
            message = payload.get('message')
            metadata = payload.get('metadata', {})
            
            logger.warning(f"Alerte système envoyée à {user_id}: {title} - {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'alerte système: {e}")
            return False
    
    def handle(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Méthode générique pour traiter un événement de notification"""
        notification_type = payload.get('notification_type')
        
        if notification_type == "share_issuance":
            return self.handle_share_issuance_notification(payload, event_id)
        elif notification_type == "certificate_generated":
            return self.handle_certificate_notification(payload, event_id)
        elif notification_type == "system_alert":
            return self.handle_system_alert(payload, event_id)
        else:
            logger.warning(f"Type de notification non reconnu: {notification_type}")
            return False


class SystemEventHandler(BaseEventHandler):
    """Handler spécialisé pour les événements système"""
    
    def handle_application_startup(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de démarrage de l'application"""
        try:
            event = payload.get('event')
            version = payload.get('version')
            environment = payload.get('environment')
            
            logger.info(f"Application démarrée - Version: {version}, Environnement: {environment}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du démarrage de l'application: {e}")
            return False
    
    def handle_database_backup(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Traite un événement de sauvegarde de base de données"""
        try:
            event = payload.get('event')
            backup_path = payload.get('backup_path')
            backup_size = payload.get('backup_size')
            
            logger.info(f"Sauvegarde de base de données créée: {backup_path} ({backup_size} bytes)")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la sauvegarde: {e}")
            return False
    
    def handle(self, payload: Dict[str, Any], event_id: str) -> bool:
        """Méthode générique pour traiter un événement système"""
        event = payload.get('event')
        
        if event == "application_startup":
            return self.handle_application_startup(payload, event_id)
        elif event == "database_backup":
            return self.handle_database_backup(payload, event_id)
        else:
            logger.warning(f"Type d'événement système non reconnu: {event}")
            return False


class EventConsumer:
    """Classe pour consommer des événements depuis RabbitMQ"""
    
    def __init__(self, host: str = 'rabbitmq', port: int = 5672,
                 username: str = 'guest', password: str = 'guest'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.running = False
        
        # Initialiser les handlers spécialisés
        self.audit_handler = AuditEventHandler()
        self.notification_handler = NotificationEventHandler()
        self.system_handler = SystemEventHandler()
        
    def connect(self):
        """Établit la connexion avec RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Déclarer les queues
            self.channel.queue_declare(queue='events', durable=True)
            self.channel.queue_declare(queue='audit_events', durable=True)
            self.channel.queue_declare(queue='notifications', durable=True)
            
            # Configuration QoS
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("Connexion RabbitMQ établie avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion RabbitMQ: {e}")
            raise
    
    def callback(self, ch, method, properties, body):
        """Callback appelé quand un message est reçu"""
        try:
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event_type')
            payload = message.get('payload', {})
            event_id = message.get('event_id')
            
            logger.info(f"Événement reçu: {event_type} (ID: {event_id})")
            
            # Router vers le handler approprié
            success = False
            if event_type in [e.value for e in EventTypeEnum]:
                success = self.audit_handler.handle(payload, event_id)
            elif event_type == "notification":
                success = self.notification_handler.handle(payload, event_id)
            elif event_type == "system":
                success = self.system_handler.handle(payload, event_id)
            else:
                logger.warning(f"Type d'événement non reconnu: {event_type}")
                success = True  # Acknowledger pour éviter les boucles infinies
            
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Événement traité avec succès: {event_type}")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.error(f"Échec du traitement de l'événement: {event_type}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self, queue_name: str = 'events'):
        """Démarre la consommation d'événements"""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            self.running = True
            logger.info(f"Démarrage de la consommation sur la queue: {queue_name}")
            
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self.callback,
                auto_ack=False
            )
            
            while self.running:
                try:
                    self.channel.start_consuming()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Erreur lors de la consommation: {e}")
                    time.sleep(5)
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la consommation: {e}")
            raise
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Ferme la connexion RabbitMQ"""
        try:
            self.running = False
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Connexion RabbitMQ fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la connexion: {e}")

# Instance globale
_consumer = None

def get_consumer() -> EventConsumer:
    """Retourne l'instance globale du consumer"""
    global _consumer
    if _consumer is None:
        _consumer = EventConsumer()
    return _consumer

def start_consumer(queue_name: str = 'events'):
    """Fonction utilitaire pour démarrer le consumer"""
    consumer = get_consumer()
    consumer.start_consuming(queue_name)


