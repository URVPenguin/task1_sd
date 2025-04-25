from time import sleep

import redis
import json
import uuid

def sync_response(pubsub):
    for message in pubsub.listen():
        if message['type'] == 'message':
            pubsub.unsubscribe()
            return json.loads(message['data'])

class InsultFilterRedisClient:
    def __init__(self, host='127.0.0.1', port=6379):
        self.redis = redis.StrictRedis(host=host, port=port, decode_responses=True)
        self.request_channel = 'insult_filter:requests'

    def submit_text(self, text):
        """Send text to be filtered"""
        response_channel = f"response:{uuid.uuid4()}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(response_channel)
        request = {
            'action': 'submit_text',
            'text': text,
            'response_channel': response_channel
        }
        self.redis.publish(self.request_channel, json.dumps(request))

        return sync_response(pubsub)

    def get_results(self):
        """Retrieve filtered results"""
        response_channel = f"response:{uuid.uuid4()}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(response_channel)

        request = {
            'action': 'get_results',
            'response_channel': response_channel
        }
        self.redis.publish(self.request_channel, json.dumps(request))

        return sync_response(pubsub)

if __name__ == '__main__':
    client = InsultFilterRedisClient()

    for i in range(10):
        print(client.submit_text("1 Hello world idiot"))
        print(client.get_results())
        sleep(1)
