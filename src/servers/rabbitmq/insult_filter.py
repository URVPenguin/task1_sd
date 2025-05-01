import threading
from collections import deque
import pika
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterRabbitMQ(InsultFilterBase):
    def __init__(self, host):
        super().__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=host,
                connection_attempts=3,
                channel_max=500))
        self.filtered_results = deque(maxlen=100)
        self.channel = self.connection.channel()

        # Exchange principal
        self.channel.exchange_declare(exchange='insult_filter', exchange_type='direct')

        # Colas para operaciones
        self.channel.queue_declare(queue='submit_text_queue')
        self.channel.queue_declare(queue='get_results_queue')

        # Bindings
        self.channel.queue_bind(exchange='insult_filter', queue='submit_text_queue', routing_key='submit_text')
        self.channel.queue_bind(exchange='insult_filter', queue='get_results_queue', routing_key='get_results')

        # Configurar consumers
        self.channel.basic_qos(prefetch_count=50)
        self.channel.basic_consume(queue='submit_text_queue', on_message_callback=self.handle_submit_text)
        self.channel.basic_consume(queue='get_results_queue', on_message_callback=self.handle_get_results)

    def process_queue(self):
        pass

    def submit_text(self, text):
        filtered = self.filter_text(text)
        self.filtered_results.append(filtered)

    def get_results(self):
        return list(self.filtered_results)

    def handle_submit_text(self, ch, method, props, body):
        """Add text to be filtered"""
        text = body.decode()
        self.submit_text(text)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body="OK"
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def handle_get_results(self, ch, method, props, body):
        results = self.get_results()
        response = "\n".join(results)

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

def run_server(host="127.0.0.1"):
    server = InsultFilterRabbitMQ(host)
    print("Running InsultFilterRabbitMQ server")
    server.channel.start_consuming()

if __name__ == "__main__":
    run_server()