import pika
import json
from datetime import datetime
from typing import Dict, Any, Callable


class NotificationSubscriber:
    """Subscriber pour recevoir des notifications"""
    
    def __init__(self, subscriber_name: str, rabbitmq_url: str = 'amqp://localhost'):
        self.subscriber_name = subscriber_name
        self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        self.channel = self.connection.channel()
        
        # Déclarer l'exchange
        self.channel.exchange_declare(exchange='notifications', exchange_type='fanout')
        
        # Créer une queue temporaire exclusive pour ce subscriber
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = result.method.queue
        
        # Lier la queue à l'exchange
        self.channel.queue_bind(exchange='notifications', queue=self.queue_name)
        
        # Handlers pour différents types de notifications
        self.handlers: Dict[str, Callable] = {}
    
    def add_handler(self, notification_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Ajouter un handler pour un type de notification"""
        self.handlers[notification_type] = handler
    
    def default_handler(self, notification: Dict[str, Any]):
        """Handler par défaut"""
        print(f" [{self.subscriber_name}] Notification reçue:")
        print(f"   Type: {notification['type']}")
        print(f"   Message: {notification['message']}")
        print(f"   Timestamp: {notification['timestamp']}")
    
    def _process_notification(self, ch, method, properties, body):
        """Traiter une notification reçue"""
        try:
            notification = json.loads(body.decode('utf-8'))
            notification_type = notification.get('type', 'info')
            
            # Utiliser le handler spécifique ou le handler par défaut
            handler = self.handlers.get(notification_type, self.default_handler)
            handler(notification)
            
            # Acquitter le message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f" Erreur lors du traitement de la notification: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Commencer à écouter les notifications"""
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._process_notification
        )
        
        print(f" [{self.subscriber_name}] En attente de notifications...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print(f"\n [{self.subscriber_name}] Arrêt du subscriber")
            self.channel.stop_consuming()
    
    def close(self):
        """Fermer la connexion"""
        self.connection.close()
