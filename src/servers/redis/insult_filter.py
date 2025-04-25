import redis
import json
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterRedis(InsultFilterBase):
    def process_queue(self):
        pass

    def submit_text(self, text):
        pass

    def get_results(self):
        pass

    def filter_text(self, text):
        pass

    def __init__(self):
        super().__init__()
        self.work_queue = "work_queue"
        self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def add_task(self, text):
        self.redis.rpush(self.work_queue, json.dumps(text))
        return True

    def process_next_task(self):
        text_json = self.redis.lpop(self.work_queue)
        if not text_json:
            return "No tasks"
        text = json.loads(text_json)
        return self.filter_text(text)

def run_server():
    client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    while True:
        message = client.blpop(queue_name, timeout=0)
        if message:
            message = message[1]
            for insult in INSULTS:
                message = message.replace(insult, "CENSORED")
            client.rpush(results, message)

if __name__ == "__main__":
    run_server()


INSULTS = ["PUTA"]
queue_name = ["work"]
results = "results_list"

