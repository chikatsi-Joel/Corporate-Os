"""
Décorateurs pour le système d'événements
"""

import functools
import logging
import asyncio
from typing import Callable, Any, Optional, Union
from .event_bus import event_bus
from .models import Event, EventType

logger = logging.getLogger(__name__)


def event_handler(event_type: Union[EventType, str], async_handler: bool = False):
    """
    Décorateur pour enregistrer un handler d'événement
    
    Args:
        event_type: Type d'événement à écouter
        async_handler: Si True, le handler est asynchrone
    
    Example:
        @event_handler(EventType.USER_LOGIN)
        def handle_user_login(event: Event):
            print(f"User logged in: {event.payload}")
            
        @event_handler(EventType.SHARE_ISSUED, async_handler=True)
        async def handle_share_issued(event: Event):
            await send_notification(event.payload)
    """
    def decorator(func: Callable) -> Callable:
        if isinstance(event_type, str):
            try:
                actual_event_type = EventType(event_type)
            except ValueError:
                logger.error(f"Type d'événement invalide: {event_type}")
                return func
        else:
            actual_event_type = event_type
        
        event_bus.subscribe(actual_event_type, func, async_handler)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def publish_event(event_type: Union[EventType, str], source: Optional[str] = None):
    """
    Décorateur pour publier automatiquement un événement après l'exécution d'une fonction
    
    Args:
        event_type: Type d'événement à publier
        source: Source de l'événement (optionnel)
    
    Example:
        @publish_event(EventType.USER_LOGIN, source="auth_service")
        def login_user(username: str, password: str):
            # Logique de connexion
            return {"user_id": "123", "username": username}
    """
    def decorator(func: Callable) -> Callable:
        if isinstance(event_type, str):
            try:
                actual_event_type = EventType(event_type)
            except ValueError:
                logger.error(f"Type d'événement invalide: {event_type}")
                return func
        else:
            actual_event_type = event_type
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            try:
                event = Event(
                    type=actual_event_type,
                    payload=result if isinstance(result, dict) else {"result": result},
                    source=source or func.__module__
                )
                event_bus.publish(event)
                logger.debug(f"Événement publié automatiquement: {event_type} depuis {func.__name__}")
            except Exception as e:
                logger.error(f"Erreur lors de la publication automatique de l'événement: {e}")
            
            return result
        
        return wrapper
    
    return decorator


def publish_event_async(event_type: Union[EventType, str], source: Optional[str] = None):
    """
    Décorateur pour publier automatiquement un événement de manière asynchrone
    
    Args:
        event_type: Type d'événement à publier
        source: Source de l'événement (optionnel)
    """
    def decorator(func: Callable) -> Callable:
        # Convertir string en EventType si nécessaire
        if isinstance(event_type, str):
            try:
                actual_event_type = EventType(event_type)
            except ValueError:
                logger.error(f"Type d'événement invalide: {event_type}")
                return func
        else:
            actual_event_type = event_type
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            try:
                event = Event(
                    type=actual_event_type,
                    payload=result if isinstance(result, dict) else {"result": result},
                    source=source or func.__module__
                )
                event_bus.publish(event)
                logger.info(f"Événement publié automatiquement (async): {event_type} depuis {func.__name__}")
            except Exception as e:
                logger.error(f"Erreur lors de la publication automatique de l'événement: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            try:
                event = Event(
                    type=actual_event_type,
                    payload=result if isinstance(result, dict) else {"result": result},
                    source=source or func.__module__
                )
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(event_bus._event_queue.put(event))
                except RuntimeError:
                    event_bus.publish(event)
                
                logger.debug(f"Événement publié automatiquement (async): {event_type} depuis {func.__name__}")
            except Exception as e:
                logger.error(f"Erreur lors de la publication automatique de l'événement: {e}")
            
            return result
        
        # Détecter si la fonction est asynchrone
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
