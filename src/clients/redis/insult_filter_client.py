from time import sleep

import redis
import json
import uuid

def sync_response(pubsub):
    for message in pubsub.listen():
        if message['type'] == 'message':
            pubsub.close()
            return json.loads(message['data'])

class InsultFilterRedisClient:
    def __init__(self, host='127.0.0.1', port=6379):
        pool = redis.ConnectionPool(host=host, port=port, db=0, decode_responses=True)
        self.redis = redis.StrictRedis(connection_pool=pool)
        self.request_queue = 'insult_filter:requests'
        self.pubsub = self.redis.pubsub()

    def send_request(self, request_data):
        response_channel = f"response:{uuid.uuid4()}"
        self.pubsub.subscribe(response_channel)

        request_data['response_channel'] = response_channel
        self.redis.rpush(self.request_queue, json.dumps(request_data))

        for message in self.pubsub.listen():
            if message['type'] == 'message':
                self.pubsub.unsubscribe(response_channel)
                return json.loads(message['data'])

    def submit_text(self, text):
        """Send text to be filtered"""
        return self.send_request({'action': 'submit_text', 'text': text})

    def get_results(self):
        """Retrieve filtered results"""
        return self.send_request({'action': 'get_results'})

    def close(self):
        self.redis.close()

if __name__ == '__main__':
    client = InsultFilterRedisClient()

    for i in range(10):
        print(client.submit_text(f"1 Hello world idiot {i}"))
        print(client.get_results())
        sleep(1)
