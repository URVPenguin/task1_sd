from xmlrpc.server import SimpleXMLRPCServer
from servers.base.insult_filter_base import InsultFilterBase

class InsultFilterXMLRPC(InsultFilterBase):
    def __init__(self):
        super().__init__()
        self.work_queue = []

    def add_task(self, text):
        self.work_queue.append(text)
        return True

    def process_next_task(self):
        if not self.work_queue:
            return "No tasks"
        text = self.work_queue.pop(0)
        filtered = self.filter_text(text)
        return filtered

def run_server():
    server = SimpleXMLRPCServer(("localhost", 8000))
    server.register_instance(InsultFilterXMLRPC())
    print("Server XML-RPC running...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()