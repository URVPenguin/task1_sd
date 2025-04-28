import threading
from time import sleep

import redis
import json
import uuid

def sync_response(pubsub):
    for message in pubsub.listen():
        if message['type'] == 'message':
            pubsub.unsubscribe()
            return json.loads(message['data'])

class InsultServiceRedisClient:
    def __init__(self, host='127.0.0.1', port=6379):
        self.redis = redis.StrictRedis(host=host, port=port, decode_responses=True)
        self.request_channel = 'insult_service:requests'
        self.notify_channel = 'insult_service:notify'

        def check_notifications():
            pubsub = self.redis.pubsub()
            pubsub.subscribe(self.notify_channel)

            for message in pubsub.listen():
                if message["type"] == "message":
                    print(message["data"])

        thread = threading.Thread(target=check_notifications, daemon=True)
        thread.start()

    def add_insult(self, insult):
        """Send text to be filtered"""
        response_channel = f"response:{uuid.uuid4()}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(response_channel)
        request = {
            'action': 'add_insult',
            'text': insult,
            'response_channel': response_channel
        }
        self.redis.publish(self.request_channel, json.dumps(request))

        return sync_response(pubsub)

    def get_all_insults(self):
        """Retrieve filtered results"""
        response_channel = f"response:{uuid.uuid4()}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(response_channel)

        request = {
            'action': 'get_all_insults',
            'response_channel': response_channel
        }
        self.redis.publish(self.request_channel, json.dumps(request))

        return sync_response(pubsub)

if __name__ == '__main__':
    client = InsultServiceRedisClient()

    print(client.add_insult("Idiot"))
    print(client.add_insult("Tonto"))
    print(client.add_insult("Burru"))
    print(client.add_insult("Capullu"))
    print(client.add_insult("Retresat"))
    print(client.get_all_insults())

    sleep(20)