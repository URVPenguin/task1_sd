import json
import signal
import sys
from collections import deque
import pika
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterRabbitMQ(InsultFilterBase):
    def __init__(self, host, port):
        super().__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.filtered_results = deque(maxlen=100)
        self.channel = self.connection.channel()
        self.should_stop = False

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
        self.submit_text_consumer_tag = self.channel.basic_consume(queue='submit_text_queue', on_message_callback=self.handle_submit_text)
        self.get_results_consumer_tag = self.channel.basic_consume(queue='get_results_queue', on_message_callback=self.handle_get_results)

    def process_queue(self):
        pass

    def submit_text(self, text):
        filtered = self.filter_text(text)
        self.filtered_results.append(filtered)

    def get_results(self):
        return list(self.filtered_results)

    def handle_submit_text(self, ch, method, props, body):
        """Add text to be filtered"""
        if self.should_stop:
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
            return

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
        if self.should_stop:
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
            return

        response = json.dumps(self.get_results())

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop_consuming(self):
        """Detiene el consumo de mensajes de manera controlada."""
        self.should_stop = True
        self.channel.basic_cancel(self.submit_text_consumer_tag)
        self.channel.basic_cancel(self.get_results_consumer_tag)

    def close(self):
        """Cierra la conexión con RabbitMQ."""
        self.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def run_server(host="127.0.0.1", port=5672):
    server = InsultFilterRabbitMQ(host, port)
    print("Running InsultFilterRabbitMQ server")

    # Manejo de señales para apagado controlado
    def signal_handler(sig, frame):
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server.channel.start_consuming()
    except KeyboardInterrupt:
        server.close()
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    run_server()