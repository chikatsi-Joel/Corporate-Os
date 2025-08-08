"""
Système d'événements léger avec annotations pour Corporate OS
"""

from .event_bus import EventBus, event_bus
from .decorators import event_handler, publish_event, publish_event_async
from .models import Event, EventType

# Importer les handlers pour qu'ils soient enregistrés
from . import handlers

__all__ = [
    'EventBus',
    'event_bus',
    'event_handler',
    'publish_event',
    'publish_event_async',
    'Event',
    'EventType'
]
