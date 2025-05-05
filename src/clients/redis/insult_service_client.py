import threading
import time
from time import sleep

import redis
import json
import uuid

class InsultServiceRedisClient:
    def __init__(self, host='127.0.0.1', port=6379):
        pool = redis.ConnectionPool(host=host, port=port, db=0, decode_responses=True)
        self.redis = redis.StrictRedis(connection_pool=pool)
        self.request_queue = 'insult_service:requests'
        self.notify_channel = 'insult_service:notify'
        self.pubsub = self.redis.pubsub()

        def check_notifications():
            try:
                pubsub = self.redis.pubsub()
                pubsub.subscribe(self.notify_channel)

                for message in pubsub.listen():
                    if message["type"] == "message":
                        print(message["data"])
            except Exception as e:
                pass

        self.thread = threading.Thread(target=check_notifications, daemon=True)
        self.thread.start()

    def send_request(self, request_data):
        response_channel = f"response:{uuid.uuid4()}"
        self.pubsub.subscribe(response_channel)

        request_data['response_channel'] = response_channel
        self.redis.rpush(self.request_queue, json.dumps(request_data))

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                self.pubsub.unsubscribe(response_channel)
                return json.loads(message['data'])

    def add_insult(self, insult):
        """Send text to be filtered"""
        return self.send_request({'action': 'add_insult', 'text': insult})
    def get_all_insults(self):
        """Retrieve filtered results"""
        return self.send_request({'action': 'get_all_insults'})

    def close(self):
        self.pubsub.close()

if __name__ == '__main__':
    client = InsultServiceRedisClient()

    print(client.add_insult("Idiot"))
    print(client.add_insult("Tonto"))
    print(client.add_insult("Burru"))
    print(client.add_insult("Capullu"))
    print(client.add_insult("Retresat"))
    print(client.get_all_insults())
    client.close()