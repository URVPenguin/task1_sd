import queue
import threading
import Pyro4
from servers.base.insult_filter_base import InsultFilterBase

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilterPyro(InsultFilterBase):
    def __init__(self):
        super().__init__()
        self.work_queue = queue.Queue()
        self.start_consumer()

    def start_consumer(self):
        """Start consumer thread to process the queue"""
        worker = threading.Thread(target=self.process_queue, daemon=True)
        worker.start()

    def process_queue(self):
        """Worker thread function to process incoming texts"""
        while True:
            try:
                text = self.work_queue.get(block=True)
                filtered_text = self.filter_text(text)
                self.results.append(filtered_text)
                self.work_queue.task_done()
            except Exception as e:
                print(f"Error processing text: {e}")

    def submit_text(self, text):
        """Add text to be filtered"""
        self.work_queue.put(text)

    def get_results(self):
        """Get all filtered results"""
        return list(self.results)

def run_server(ns="pyro.insult_filter"):
    daemon = Pyro4.Daemon()
    uri = daemon.register(InsultFilterPyro)
    Pyro4.locateNS().register(ns, uri)
    print("Running InsultFilterPyro server: ", uri)
    daemon.requestLoop()

if __name__ == "__main__":
    run_server()