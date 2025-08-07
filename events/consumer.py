import pika

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='events')

    def callback(ch, method, properties, body):
        print(f"Reçu: {body}")

    channel.basic_consume(queue='events', on_message_callback=callback, auto_ack=True)
    print('En attente des événements...')
    channel.start_consuming()