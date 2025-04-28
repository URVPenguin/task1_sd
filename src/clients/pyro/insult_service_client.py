import threading
from time import sleep

import Pyro4

class NotificationServer:
    @Pyro4.expose
    def notify(self, insult):
        print(insult)

class InsultServicePyroClient:
    def __init__(self, ns="pyro.insult_service"):
        uri = Pyro4.locateNS().lookup(ns)
        self.server = Pyro4.Proxy(uri)

        def listen_notifications():
            with Pyro4.Daemon() as daemon:
                notify_uri = daemon.register(NotificationServer())
                self.server.register_subscriber(notify_uri)
                daemon.requestLoop()

        t = threading.Thread(target=listen_notifications, daemon=True)
        t.start()

    def add_insult(self, insult):
        """Submit text for filtering"""
        self.server.add_insult(insult)

    def get_all_insults(self):
        """Get filtered results"""
        return self.server.get_all_insults()

if __name__ == "__main__":
    client = InsultServicePyroClient()

    client.add_insult("idiot")
    client.add_insult("stupid")
    client.add_insult("stupid")
    client.add_insult("retardet")

    sleep(5)

    print(client.get_all_insults())