import json

import redis
from threading import Thread, Event
from servers.base.insult_service_base import InsultServiceBase

class InsultServiceRedis(InsultServiceBase):
    def __init__(self, host, port):
        super().__init__()
        self.redis = redis.Redis(host=host, port=port, db=0, decode_responses=True)
        self.insults = 'insult_service:insults'
        self.request_channel = 'insult_service:requests'
        self.notify_channel = "insult_service:notify"
        self.start_broadcaster()

    def process_request(self, request_data):
        """Process a client request"""
        if request_data['action'] == 'add_insult':
            try:
                self.add_insult(request_data['text'])
                return {'status': 'success'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

        elif request_data['action'] == 'get_all_insults':
            try:
                return {'status': 'success', 'results': self.get_all_insults()}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        elif request_data['action'] == 'get_all_insults':
            try:
                return {'status': 'success', 'results': self.get_all_insults()}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return {'status': 'error', 'message': 'Invalid action'}

    def add_insult(self, insult: str):
        """Add insult if not already present"""
        self.redis.sadd(self.insults, insult)

    def get_all_insults(self):
        """Return all stored insults"""
        return list(self.redis.smembers(self.insults))

    def unregister_subscriber(self, callback_url: str):
        pass

    def register_subscriber(self, callback_url: str):
        pass

    def start_broadcaster(self, interval: int = 5):
        """Start broadcasting random insults periodically"""
        def broadcaster_loop():
            while not Event().wait(interval):
                insult = self.redis.srandmember(self.insults)
                if insult:
                    self.notify_subscribers(insult)

        broadcaster_thread = Thread(target=broadcaster_loop, daemon=True)
        broadcaster_thread.start()

    def stop_broadcaster(self):
        """Stop the insult broadcaster"""
        pass

    def notify_subscribers(self, insult: str):
        self.redis.publish(self.notify_channel, insult)

def run_server(host="127.0.0.1", port=6379):
    service = InsultServiceRedis(host, port)

    pubsub = service.redis.pubsub()
    pubsub.subscribe(service.request_channel)

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                request = json.loads(message['data'])
                response = service.process_request(request)
                service.redis.publish(request['response_channel'], json.dumps(response))
            except Exception as e:
                error_response = {'status': 'error', 'message': str(e)}
                if 'response_channel' in request:
                    service.redis.publish(request['response_channel'], json.dumps(error_response))

if __name__ == "__main__":
    run_server()