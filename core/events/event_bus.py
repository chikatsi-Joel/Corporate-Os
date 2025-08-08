"""
Bus d'événements léger pour Corporate OS
"""

import asyncio
import threading
import logging
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from datetime import datetime

from .models import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Bus d'événements léger et asynchrone"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._async_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, handler: Callable, async_handler: bool = False):
        """
        S'abonne à un type d'événement
        
        Args:
            event_type: Type d'événement
            handler: Fonction de traitement
            async_handler: Si True, le handler est asynchrone
        """
        with self._lock:
            if async_handler:
                self._async_handlers[event_type].append(handler)
                logger.debug(f"Handler asynchrone enregistré pour: {event_type}")
            else:
                self._handlers[event_type].append(handler)
                logger.debug(f"Handler synchrone enregistré pour: {event_type}")

    
    def unsubscribe(self, event_type: EventType, handler: Callable, async_handler: bool = False):
        """
        Se désabonne d'un type d'événement
        
        Args:
            event_type: Type d'événement
            handler: Fonction de traitement à retirer
            async_handler: Si True, le handler est asynchrone
        """
        with self._lock:
            if async_handler:
                if handler in self._async_handlers[event_type]:
                    self._async_handlers[event_type].remove(handler)
                    logger.debug(f"Handler asynchrone retiré pour: {event_type}")
            else:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    logger.debug(f"Handler synchrone retiré pour: {event_type}")

    
    def publish(self, event: Event) -> bool:
        """
        Publie un événement de manière non-bloquante
        
        Args:
            event: L'événement à publier
            
        Returns:
            True si l'événement a été ajouté à la queue
        """
        try:
            # Traitement synchrone immédiat
            self._handle_sync(event)
            
            # Ajout à la queue pour traitement asynchrone
            if self._async_handlers[event.type]:
                asyncio.create_task(self._event_queue.put(event))
            
            logger.info(f"Événement publié: {event.type} (ID: {event.id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication de l'événement: {e}")
            return False
    
    def _handle_sync(self, event: Event):
        """Traite un événement de manière synchrone"""
        handlers = self._handlers.get(event.type, [])
        
        for handler in handlers:
            try:
                result = handler(event)
                if result is False:
                    logger.warning(f"Handler synchrone a échoué pour l'événement: {event.type}")
            except Exception as e:
                logger.error(f"Erreur dans le handler synchrone pour {event.type}: {e}")
    
    
    async def _handle_async(self, event: Event):
        """Traite un événement de manière asynchrone"""
        handlers = self._async_handlers.get(event.type, [])
        
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                else:
                    # Exécuter dans un thread pool si ce n'est pas une coroutine
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(None, handler, event)
                    tasks.append(task)
            except Exception as e:
                logger.error(f"Erreur lors de la création de la tâche pour {event.type}: {e}")
        
        # Attendre que toutes les tâches se terminent
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Erreur dans le handler asynchrone {i} pour {event.type}: {result}")
                elif result is False:
                    logger.warning(f"Handler asynchrone {i} a échoué pour l'événement: {event.type}")
    
    async def _worker_loop(self):
        """Boucle principale du worker asynchrone"""
        while self._running:
            try:
                # Attendre un événement avec timeout
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                    await self._handle_async(event)
                    self._event_queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Erreur dans la boucle worker: {e}")
                    
            except Exception as e:
                logger.error(f"Erreur critique dans la boucle worker: {e}")
                await asyncio.sleep(1)
    
    def start(self):
        """Démarre le bus d'événements"""
        if not self._running:
            self._running = True
            try:
                loop = asyncio.get_event_loop()
                self._worker_task = loop.create_task(self._worker_loop())
                logger.info("Bus d'événements démarré")
            except RuntimeError:
                def run_worker():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._worker_loop())
                
                worker_thread = threading.Thread(target=run_worker, daemon=True)
                worker_thread.start()
                logger.info("Bus d'événements démarré dans un thread séparé")
    
    def stop(self):
        """Arrête le bus d'événements"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        logger.info("Bus d'événements arrêté")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du bus d'événements"""
        return {
            "running": self._running,
            "queue_size": self._event_queue.qsize(),
            "sync_handlers": {k.value: len(v) for k, v in self._handlers.items()},
            "async_handlers": {k.value: len(v) for k, v in self._async_handlers.items()}
        }


# Instance globale du bus d'événements
event_bus = EventBus()
