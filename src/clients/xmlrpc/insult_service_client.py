from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import threading

class InsultServiceXMLRPCClient:
    def __init__(self, server_url: str):
        self.server = ServerProxy(server_url)

    def listen(self, client_port):
        """Inicia el servidor RPC para recibir insultos"""

        def run_client_server():
            with SimpleXMLRPCServer(("localhost", client_port), allow_none=True) as server_subs:
                server_subs.register_instance(self)
                server_subs.timeout = 5
                while getattr(threading.current_thread(), "do_run", True):
                    server_subs.handle_request()

        t = threading.Thread(target=run_client_server, daemon=False)
        t.do_run = True
        t.start()

        callback_url = f"http://localhost:{client_port}"
        if self.server.register_subscriber(callback_url):
            print("Successfully registered as subscriber")
        else:
            print("Registration failed")

        return t

    def notify(self, insult: str):
        """Método llamado por el servidor para enviar insultos"""
        print(f"Received insult: {insult}")