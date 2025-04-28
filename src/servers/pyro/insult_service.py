import random
import threading
import time

import Pyro4
from servers.base.insult_service_base import InsultServiceBase

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServicePyro(InsultServiceBase):
    def __init__(self):
        super().__init__()
        self.subscribers = []
        self.broadcaster_thread = None

    def add_insult(self, insult: str):
        if insult not in self.insults:
            self.insults.append(insult)

    def get_all_insults(self):
        return self.insults

    def register_subscriber(self, subscriber):
        self.subscribers.append(subscriber)
        if len(self.subscribers) == 1:
            self.start_broadcaster()

    def unregister_subscriber(self, subscriber):
        self.subscribers.remove(subscriber)

        if self.subscribers is None and self.broadcaster_thread:
           self.stop_broadcaster()

    def start_broadcaster(self, interval: int = 5):
        def broadcaster_loop():
            while True:
                time.sleep(interval)
                if self.insults:
                    insult = random.choice(self.insults)
                    self.notify_subscribers(insult)

        broadcaster_thread = threading.Thread(target=broadcaster_loop, daemon=True)
        broadcaster_thread.start()

    def stop_broadcaster(self):
        if self.broadcaster_thread:
            self.broadcaster_thread.join()

    def notify_subscribers(self, insult: str):
        for subscriber in self.subscribers:
            try:
                print(f"Entra {subscriber}")
                Pyro4.Proxy(subscriber).notify(insult)
            except Exception:
                print(f"Communication error to => {subscriber}")
                self.unregister_subscriber(subscriber)
                print(self.subscribers)

def run_server(ns="pyro.insult_service"):
    daemon = Pyro4.Daemon()
    uri = daemon.register(InsultServicePyro)
    Pyro4.locateNS().register(ns, uri)
    print("Running InsultServicePyro server: ", uri)
    daemon.requestLoop()

if __name__ == "__main__":
    run_server()