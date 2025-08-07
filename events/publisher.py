import pika

def publish_event(event_type: str, payload: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='events')
    message = {
        "type": event_type,
        "payload": payload
    }
    channel.basic_publish(
        exchange='',
        routing_key='events',
        body=str(message)
    )
    connection.close()