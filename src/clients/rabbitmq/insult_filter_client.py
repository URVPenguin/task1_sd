import json
import time
import uuid
import pika

class InsultFilterRabbitMQClient:
    def __init__(self, host = "127.0.0.1", port = 5672):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, port))
        self.channel = self.connection.channel()
        self.callback_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)
        self.responses = {}

    def on_response(self, ch, method, props, body):
        """Maneja respuestas RPC"""
        if props.correlation_id in self.responses:
            self.responses[props.correlation_id] = body.decode()

    def submit_text(self, text):
        """Envía texto para ser filtrado (no devuelve el resultado filtrado)"""
        self.call_rpc_method('insult_filter', 'submit_text', text)

    def get_results(self):
        """Obtiene todos los textos filtrados acumulados"""
        return json.loads(self.call_rpc_method('insult_filter', 'get_results'))

    def call_rpc_method(self, exchange, routing_key, body=""):
        """Realiza una llamada RPC genérica"""
        corr_id = str(uuid.uuid4())
        self.responses[corr_id] = None

        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=corr_id,
                delivery_mode=1,

            ),
            body=body.encode() if body else ''
        )

        start_time = time.time()
        while self.responses[corr_id] is None:
            self.connection.process_data_events()
            if time.time() - start_time > 5:
                raise TimeoutError("No response received")

        return self.responses.pop(corr_id)

if __name__ == "__main__":
    client = InsultFilterRabbitMQClient()
    client.submit_text("Hello world idiot")
    client.submit_text("Hello world stupid")
    time.sleep(1)
    print(client.get_results())
