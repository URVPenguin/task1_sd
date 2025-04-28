import threading
import redis
import json
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterRedis(InsultFilterBase):
    def __init__(self, host, port):
        super().__init__()
        self.redis = redis.Redis(host=host, port=port, db=0, decode_responses=True)
        self.work_queue = 'insult_filter:work_queue'
        self.results = 'insult_filter:results'
        self.request_channel = 'insult_filter:requests'
        self.start_consumer()

    def start_consumer(self):
        """Start consumer thread to process the queue"""
        worker = threading.Thread(target=self.process_queue, daemon=True)
        worker.start()

    def process_request(self, request_data):
        """Process a client request"""
        if request_data['action'] == 'submit_text':
            try:
                self.submit_text(request_data['text'])
                return {'status': 'success'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

        elif request_data['action'] == 'get_results':
            try:
                return {'status': 'success', 'results': self.get_results()}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        else:
            return {'status': 'error', 'message': 'Invalid action'}

    def process_queue(self):
        """Worker thread function to process incoming texts"""
        while True:
            try:
                _, text = self.redis.blpop([self.work_queue], timeout=0)
                filtered_text = self.filter_text(text)
                self.redis.rpush(self.results, filtered_text)
            except Exception as e:
                print(f"Error processing text: {e}")

    def submit_text(self, text):
        self.redis.rpush(self.work_queue, json.dumps(text))

    def get_results(self):
        return self.redis.lrange(self.results, -100, -1)


def run_server(host="127.0.0.1", port=6379):
    service = InsultFilterRedis(host, port)

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