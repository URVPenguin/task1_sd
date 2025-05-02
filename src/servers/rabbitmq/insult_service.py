import json
import random
import threading
import time
import pika

from servers.base.insult_service_base import InsultServiceBase

class InsultServiceRabbitMQ(InsultServiceBase):
    def __init__(self, host, port):
        super().__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.broadcast_connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.channel = self.connection.channel()
        self.broadcast_channel = self.broadcast_connection.channel()

        # Configuración de exchanges y colas
        self.channel.exchange_declare(exchange='insult_service', exchange_type='direct')
        self.broadcast_channel.exchange_declare(exchange='insult_broadcast', exchange_type='fanout')

        # Colas para diferentes operaciones
        self.channel.queue_declare(queue='add_insult_queue')
        self.channel.queue_declare(queue='get_all_insults_queue')

        # Bindings
        self.channel.queue_bind(exchange='insult_service', queue='add_insult_queue', routing_key='add_insult')
        self.channel.queue_bind(exchange='insult_service', queue='get_all_insults_queue',
                                routing_key='get_all_insults')

        # Consumers
        self.channel.basic_qos(prefetch_count=100)
        self.channel.basic_consume(queue='add_insult_queue', on_message_callback=self.handle_add_insult)
        self.channel.basic_consume(queue='get_all_insults_queue', on_message_callback=self.handle_get_all_insults)

        self.broadcaster_thread = None
        self.start_broadcaster()

    def add_insult(self, insult: str):
        if insult not in self.insults:
            self.insults.append(insult)

    def get_all_insults(self):
        return self.insults

    def unregister_subscriber(self, subscriber_queue):
        pass
    def register_subscriber(self, subscriber_queue):
        pass

    def start_broadcaster(self, interval: int = 5):
        def broadcaster_loop():
            while True:
                try:
                    if self.insults:
                        insult = random.choice(self.insults)
                        self.notify_subscribers(insult)
                except Exception as e:
                    print("con lost", e)

                time.sleep(interval)

        self.broadcaster_thread = threading.Thread(target=broadcaster_loop, daemon=True)
        self.broadcaster_thread.start()

    def stop_broadcaster(self):
        pass

    def notify_subscribers(self, insult: str):
        self.broadcast_channel.basic_publish(exchange='insult_broadcast', routing_key='', body=insult)

    def handle_add_insult(self, ch, method, props, body):
        insult = body.decode()
        self.add_insult(insult)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body="OK"
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def handle_get_all_insults(self, ch, method, props, body):
        response = json.dumps(self.get_all_insults())
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

def run_server(host="127.0.0.1", port=5672):
    server = InsultServiceRabbitMQ(host, port)
    print("Running InsultServiceRabbitMQ server")
    server.channel.start_consuming()

if __name__ == "__main__":
    run_server()