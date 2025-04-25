from xmlrpc.server import SimpleXMLRPCServer
from threading import Thread, Event
import random
from typing import List
from xmlrpc.client import ServerProxy
from servers.base.insult_service_base import InsultServiceBase


class InsultServiceXMLRPC(InsultServiceBase):
    def __init__(self):
        super().__init__()
        self.insults: List[str] = []
        self.subscribers: List[str] = []
        self.broadcaster_thread = None
        self.stop_event = Event()

    # Métodos básicos RPC
    def add_insult(self, insult: str) -> bool:
        """Añade un insulto a la lista si no existe"""
        if insult not in self.insults:
            self.insults.append(insult)
            return True
        return False

    def get_all_insults(self) -> List[str]:
        """Devuelve todos los insultos almacenados"""
        return self.insults.copy()

    # Sistema de broadcasting
    def register_subscriber(self, callback_url: str) -> bool:
        """Registra un cliente para recibir insultos aleatorios"""
        if callback_url not in self.subscribers:
            self.subscribers.append(callback_url)

            # Inicia el broadcaster si es el primer subscriptor
            if len(self.subscribers) == 1:
                self.start_broadcaster()

            return True
        return False

    def unregister_subscriber(self, callback_url: str) -> bool:
        """Elimina un cliente de la lista de subscriptores"""
        if callback_url in self.subscribers:
            self.subscribers.remove(callback_url)

            # Detiene el broadcaster si no hay subscriptores
            if not self.subscribers and self.broadcaster_thread:
                self.stop_broadcaster()

            return True
        return False

    def start_broadcaster(self, interval: int = 5) -> None:
        """Inicia el hilo que envía insultos cada 5 segundos"""
        self.stop_event.clear()

        def broadcaster_loop():
            while not self.stop_event.wait(interval):
                if self.insults:
                    insult = random.choice(self.insults)
                    self.notify_subscribers(insult)

        self.broadcaster_thread = Thread(target=broadcaster_loop, daemon=True)
        self.broadcaster_thread.start()

    def stop_broadcaster(self):
        """Detiene el hilo de broadcasting"""
        self.stop_event.set()
        if self.broadcaster_thread:
            self.broadcaster_thread.join()

    def notify_subscribers(self, insult: str):
        """Notifica a todos los clientes registrados"""
        for subscriber_url in self.subscribers[:]:
            try:
                proxy = ServerProxy(subscriber_url)
                proxy.notify(insult)
            except Exception as e:
                print(f"Error notifying {subscriber_url}: {e}")
                self.subscribers.remove(subscriber_url)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server = SimpleXMLRPCServer((host, port))
    service = InsultServiceXMLRPC()
    server.register_instance(service)
    print(f"InsultServiceXMLRPC running on {host}:{port}")
    print("Broadcasting insults every 5 seconds to registered clients")
    server.serve_forever()


if __name__ == "__main__":
    run_server()