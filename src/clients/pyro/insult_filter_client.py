import Pyro4

class InsultFilterPyroClient:
    def __init__(self, ns="pyro.insult_filter"):
        uri = Pyro4.locateNS().lookup(ns)
        self.server = Pyro4.Proxy(uri)

    def submit_text(self, text):
        """Submit text for filtering"""
        self.server.submit_text(text)

    def get_results(self):
        """Get filtered results"""
        return self.server.get_results()

if __name__ == "__main__":
    client = InsultFilterPyroClient()

    client.submit_text("Hello world idiot")
    client.submit_text("Hello world stupid")
    print(client.get_results())
