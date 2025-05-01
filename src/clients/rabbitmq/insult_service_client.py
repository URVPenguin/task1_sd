import json
import time
import uuid
from time import sleep

import pika

class InsultServiceRabbitMQClient:
    def __init__(self, host = "127.0.0.1"):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='insult_broadcast', exchange_type='fanout')

        self.callback_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.broadcast_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue

        self.channel.queue_bind(queue=self.broadcast_queue, exchange='insult_broadcast')
        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)
        self.channel.basic_consume(queue=self.broadcast_queue, on_message_callback=self.recive_insult, auto_ack=True)

        self.responses = {}

    def recive_insult(self, ch, method, props, body):
        print(body.decode())

    def on_response(self, ch, method, props, body):
        if props.correlation_id in self.responses:
            self.responses[props.correlation_id] = body.decode()

    def add_insult(self, insult):
        self.call_rpc_method('insult_service', 'add_insult', insult)

    def get_all_insults(self):
        return json.loads(self.call_rpc_method('insult_service', 'get_all_insults'))

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
    client = InsultServiceRabbitMQClient()
    client.add_insult("idiot adasdf ad fasd a")
    client.add_insult("retardet")
    client.add_insult("down")
    client.add_insult("mongolish")
    print(client.get_all_insults())
    while True:
        client.add_insult("stupid")
        sleep(3)

