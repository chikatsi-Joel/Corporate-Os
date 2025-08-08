"""
Module events - Gestion des événements avec RabbitMQ
"""

from .publisher import (
    get_audit_publisher,
    get_notification_publisher,
    get_system_publisher,
    AuditEventPublisher,
    NotificationEventPublisher,
    SystemEventPublisher
)
from .consumer import (
    start_consumer,
    get_consumer,
    EventConsumer,
    AuditEventHandler,
    NotificationEventHandler,
    SystemEventHandler
)

__all__ = [
    'get_audit_publisher',
    'get_notification_publisher', 
    'get_system_publisher',
    'AuditEventPublisher',
    'NotificationEventPublisher',
    'SystemEventPublisher',
    'start_consumer',
    'get_consumer',
    'EventConsumer',
    'AuditEventHandler',
    'NotificationEventHandler',
    'SystemEventHandler'
]


