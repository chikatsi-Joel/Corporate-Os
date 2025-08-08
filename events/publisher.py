"""
Publisher d'événements pour RabbitMQ
Gère l'envoi d'événements vers la queue RabbitMQ avec des publishers spécialisés
"""

import pika
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from abc import ABC, abstractmethod

from core.event_type import EventTypeEnum

logger = logging.getLogger(__name__)


class BasePublisher(ABC):
    """Classe de base pour les publishers d'événements"""
    
    def __init__(self, host: str = 'rabbitmq', port: int = 5672, 
                 username: str = 'guest', password: str = 'guest'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        
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
            
            # Déclarer les queues et exchanges
            self._declare_queues_and_exchanges()
            
            logger.info("Connexion RabbitMQ établie avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion RabbitMQ: {e}")
            raise
    
    def _declare_queues_and_exchanges(self):
        """Déclare les queues et exchanges nécessaires"""
        # Déclarer les queues
        self.channel.queue_declare(queue='events', durable=True)
        self.channel.queue_declare(queue='audit_events', durable=True)
        self.channel.queue_declare(queue='notifications', durable=True)
        
        # Déclarer l'exchange pour les événements
        self.channel.exchange_declare(
            exchange='corporate_os_events',
            exchange_type='topic',
            durable=True
        )
        
        # Binding des queues à l'exchange
        self.channel.queue_bind(
            exchange='corporate_os_events',
            queue='events',
            routing_key='events.*'
        )
        
        self.channel.queue_bind(
            exchange='corporate_os_events',
            queue='audit_events',
            routing_key='audit.*'
        )
        
        self.channel.queue_bind(
            exchange='corporate_os_events',
            queue='notifications',
            routing_key='notification.*'
        )
    
    def disconnect(self):
        """Ferme la connexion RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Connexion RabbitMQ fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la connexion: {e}")
    
    def _publish_message(self, message: Dict[str, Any], routing_key: str) -> bool:
        """
        Publie un message vers RabbitMQ
        
        Args:
            message: Message à publier
            routing_key: Clé de routage
            
        Returns:
            bool: True si le message a été publié avec succès
        """
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            self.channel.basic_publish(
                exchange='corporate_os_events',
                routing_key=routing_key,
                body=json.dumps(message, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Message persistant
                    content_type='application/json'
                )
            )
            
            logger.info(f"Message publié avec routing_key: {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication du message: {e}")
            return False
    
    @abstractmethod
    def publish(self, **kwargs) -> bool:
        """Méthode abstraite pour publier un événement"""
        pass


class AuditEventPublisher(BasePublisher):
    """Publisher spécialisé pour les événements d'audit"""
    
    def publish_user_login(self, user_id: str, user_email: str, user_role: str, 
                          ip_address: str = None, user_agent: str = None) -> bool:
        """Publie un événement de connexion utilisateur"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.USER_LOGIN.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "user_email": user_email,
                "user_role": user_role,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        }
        
        return self._publish_message(message, "audit.user.login")
    
    def publish_user_logout(self, user_id: str, user_email: str, 
                           session_duration: int = None) -> bool:
        """Publie un événement de déconnexion utilisateur"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.USER_LOGOUT.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "user_email": user_email,
                "session_duration": session_duration
            }
        }
        
        return self._publish_message(message, "audit.user.logout")
    
    def publish_shareholder_created(self, user_id: str, shareholder_data: Dict[str, Any]) -> bool:
        """Publie un événement de création d'actionnaire"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.SHAREHOLDER_CREATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "shareholder_data": shareholder_data
            }
        }
        
        return self._publish_message(message, "audit.shareholder.created")
    
    def publish_shareholder_updated(self, user_id: str, shareholder_id: str, 
                                   previous_data: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
        """Publie un événement de mise à jour d'actionnaire"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.SHAREHOLDER_UPDATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "shareholder_id": shareholder_id,
                "previous_data": previous_data,
                "new_data": new_data
            }
        }
        
        return self._publish_message(message, "audit.shareholder.updated")
    
    def publish_share_issued(self, user_id: str, shareholder_id: str, 
                            share_data: Dict[str, Any]) -> bool:
        """Publie un événement d'émission d'actions"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.SHARE_ISSUED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "shareholder_id": shareholder_id,
                "share_data": share_data
            }
        }
        
        return self._publish_message(message, "audit.share.issued")
    
    def publish_certificate_generated(self, user_id: str, shareholder_id: str, 
                                     certificate_path: str) -> bool:
        """Publie un événement de génération de certificat"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.CERTIFICATE_GENERATED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "shareholder_id": shareholder_id,
                "certificate_path": certificate_path
            }
        }
        
        return self._publish_message(message, "audit.certificate.generated")
    
    def publish_permission_changed(self, admin_user_id: str, target_user_id: str, 
                                  old_role: str, new_role: str) -> bool:
        """Publie un événement de changement de permission"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.PERMISSION_CHANGED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "admin_user_id": admin_user_id,
                "target_user_id": target_user_id,
                "old_role": old_role,
                "new_role": new_role
            }
        }
        
        return self._publish_message(message, "audit.permission.changed")
    
    def publish_data_export(self, user_id: str, export_type: str, 
                           export_format: str, record_count: int) -> bool:
        """Publie un événement d'export de données"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.DATA_EXPORT.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "export_type": export_type,
                "export_format": export_format,
                "record_count": record_count
            }
        }
        
        return self._publish_message(message, "audit.data.export")
    
    def publish_system_error(self, error_type: str, error_message: str, 
                            stack_trace: str = None) -> bool:
        """Publie un événement d'erreur système"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": EventTypeEnum.SYSTEM_ERROR.value,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace
            }
        }
        
        return self._publish_message(message, "audit.system.error")
    
    def publish(self, **kwargs) -> bool:
        """Méthode générique pour publier un événement d'audit"""
        event_type = kwargs.get('event_type')
        
        if event_type == EventTypeEnum.USER_LOGIN.value:
            return self.publish_user_login(
                kwargs['user_id'], kwargs['user_email'], kwargs['user_role'],
                kwargs.get('ip_address'), kwargs.get('user_agent')
            )
        elif event_type == EventTypeEnum.USER_LOGOUT.value:
            return self.publish_user_logout(
                kwargs['user_id'], kwargs['user_email'], kwargs.get('session_duration')
            )
        elif event_type == EventTypeEnum.SHAREHOLDER_CREATED.value:
            return self.publish_shareholder_created(
                kwargs['user_id'], kwargs['shareholder_data']
            )
        elif event_type == EventTypeEnum.SHAREHOLDER_UPDATED.value:
            return self.publish_shareholder_updated(
                kwargs['user_id'], kwargs['shareholder_id'], 
                kwargs['previous_data'], kwargs['new_data']
            )
        elif event_type == EventTypeEnum.SHARE_ISSUED.value:
            return self.publish_share_issued(
                kwargs['user_id'], kwargs['shareholder_id'], kwargs['share_data']
            )
        elif event_type == EventTypeEnum.CERTIFICATE_GENERATED.value:
            return self.publish_certificate_generated(
                kwargs['user_id'], kwargs['shareholder_id'], kwargs['certificate_path']
            )
        elif event_type == EventTypeEnum.PERMISSION_CHANGED.value:
            return self.publish_permission_changed(
                kwargs['admin_user_id'], kwargs['target_user_id'],
                kwargs['old_role'], kwargs['new_role']
            )
        elif event_type == EventTypeEnum.DATA_EXPORT.value:
            return self.publish_data_export(
                kwargs['user_id'], kwargs['export_type'], 
                kwargs['export_format'], kwargs['record_count']
            )
        elif event_type == EventTypeEnum.SYSTEM_ERROR.value:
            return self.publish_system_error(
                kwargs['error_type'], kwargs['error_message'], kwargs.get('stack_trace')
            )
        else:
            logger.error(f"Type d'événement d'audit non reconnu: {event_type}")
            return False


class NotificationEventPublisher(BasePublisher):
    """Publisher spécialisé pour les événements de notification"""
    
    def publish_share_issuance_notification(self, user_id: str, shareholder_name: str, 
                                           share_count: int, total_amount: float) -> bool:
        """Publie un événement de notification d'émission d'actions"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "notification",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "notification_type": "share_issuance",
                "title": "Nouvelle émission d'actions",
                "message": f"Une émission de {share_count} actions pour {total_amount}€ a été créée pour {shareholder_name}",
                "metadata": {
                    "shareholder_name": shareholder_name,
                    "share_count": share_count,
                    "total_amount": total_amount
                }
            }
        }
        
        return self._publish_message(message, "notification.share.issuance")
    
    def publish_certificate_notification(self, user_id: str, certificate_path: str) -> bool:
        """Publie un événement de notification de certificat généré"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "notification",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "notification_type": "certificate_generated",
                "title": "Certificat d'actions généré",
                "message": "Votre certificat d'actions a été généré avec succès",
                "metadata": {
                    "certificate_path": certificate_path
                }
            }
        }
        
        return self._publish_message(message, "notification.certificate.generated")
    
    def publish_system_alert(self, user_id: str, alert_type: str, alert_message: str) -> bool:
        """Publie un événement d'alerte système"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "notification",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "user_id": user_id,
                "notification_type": "system_alert",
                "title": f"Alerte système - {alert_type}",
                "message": alert_message,
                "metadata": {
                    "alert_type": alert_type
                }
            }
        }
        
        return self._publish_message(message, "notification.system.alert")
    
    def publish(self, **kwargs) -> bool:
        """Méthode générique pour publier un événement de notification"""
        notification_type = kwargs.get('notification_type')
        
        if notification_type == "share_issuance":
            return self.publish_share_issuance_notification(
                kwargs['user_id'], kwargs['shareholder_name'],
                kwargs['share_count'], kwargs['total_amount']
            )
        elif notification_type == "certificate_generated":
            return self.publish_certificate_notification(
                kwargs['user_id'], kwargs['certificate_path']
            )
        elif notification_type == "system_alert":
            return self.publish_system_alert(
                kwargs['user_id'], kwargs['alert_type'], kwargs['alert_message']
            )
        else:
            logger.error(f"Type de notification non reconnu: {notification_type}")
            return False


class SystemEventPublisher(BasePublisher):
    """Publisher spécialisé pour les événements système"""
    
    def publish_application_startup(self, version: str, environment: str) -> bool:
        """Publie un événement de démarrage de l'application"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "event": "application_startup",
                "version": version,
                "environment": environment
            }
        }
        
        return self._publish_message(message, "system.application.startup")
    
    def publish_database_backup(self, backup_path: str, backup_size: int) -> bool:
        """Publie un événement de sauvegarde de base de données"""
        message = {
            "event_id": str(uuid.uuid4()),
            "event_type": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "event": "database_backup",
                "backup_path": backup_path,
                "backup_size": backup_size
            }
        }
        
        return self._publish_message(message, "system.database.backup")
    
    def publish(self, **kwargs) -> bool:
        """Méthode générique pour publier un événement système"""
        event = kwargs.get('event')
        
        if event == "application_startup":
            return self.publish_application_startup(
                kwargs['version'], kwargs['environment']
            )
        elif event == "database_backup":
            return self.publish_database_backup(
                kwargs['backup_path'], kwargs['backup_size']
            )
        else:
            logger.error(f"Type d'événement système non reconnu: {event}")
            return False


# Instances globales des publishers
_audit_publisher = None
_notification_publisher = None
_system_publisher = None

def get_audit_publisher() -> AuditEventPublisher:
    """Retourne l'instance globale du publisher d'audit"""
    global _audit_publisher
    if _audit_publisher is None:
        _audit_publisher = AuditEventPublisher()
    return _audit_publisher

def get_notification_publisher() -> NotificationEventPublisher:
    """Retourne l'instance globale du publisher de notifications"""
    global _notification_publisher
    if _notification_publisher is None:
        _notification_publisher = NotificationEventPublisher()
    return _notification_publisher

def get_system_publisher() -> SystemEventPublisher:
    """Retourne l'instance globale du publisher système"""
    global _system_publisher
    if _system_publisher is None:
        _system_publisher = SystemEventPublisher()
    return _system_publisher

# Fonctions utilitaires pour la compatibilité avec l'ancien code
def publish_audit_event(user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: dict) -> bool:
    """Fonction utilitaire pour publier un événement d'audit (compatibilité)"""
    publisher = get_audit_publisher()
    return publisher.publish(
        event_type=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        **details
    )

def publish_notification_event(user_id: str, notification_type: str, 
                              message: str, metadata: dict) -> bool:
    """Fonction utilitaire pour publier un événement de notification (compatibilité)"""
    publisher = get_notification_publisher()
    return publisher.publish(
        notification_type=notification_type,
        user_id=user_id,
        message=message,
        **metadata
    )


