import xmlrpc.client

class InsultFilterXMLRPClient:
    def __init__(self, server_url='http://localhost:8000'):
        self.server = xmlrpc.client.ServerProxy(server_url)

    def submit_text(self, text):
        """Submit text for filtering"""
        return self.server.submit_text(text)

    def get_results(self):
        """Get filtered results"""
        return len(self.server.get_results())

    def get_queue_status(self):
        """Check how many items are in the queue"""
        return self.server.get_queue_size()