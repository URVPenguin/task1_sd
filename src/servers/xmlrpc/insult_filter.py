import queue
from xmlrpc.server import SimpleXMLRPCServer
import threading
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterXMLRPCServer(InsultFilterBase):
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
        """Add text to the processing queue"""
        self.work_queue.put(text)
        return True

    def get_results(self):
        """Retrieve filtered results"""
        return list(self.results)


def run_server(host='127.0.0.1', port=8000):
    server = SimpleXMLRPCServer((host, port), allow_none=True)
    server.register_instance(InsultFilterXMLRPCServer())
    print(f"InsultFilterXMLRPCServer running on {host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()