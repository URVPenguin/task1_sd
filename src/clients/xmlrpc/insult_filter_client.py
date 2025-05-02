import xmlrpc.client

class InsultFilterXMLRPClient:
    def __init__(self, host='127.0.0.1', server_port = 8000):
        self.server = xmlrpc.client.ServerProxy("http://{}:{}".format(host, server_port))

    def submit_text(self, text):
        """Submit text for filtering"""
        return self.server.submit_text(text)

    def get_results(self):
        """Get filtered results"""
        return self.server.get_results()