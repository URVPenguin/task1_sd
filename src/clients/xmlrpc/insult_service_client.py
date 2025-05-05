from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import threading

class InsultServiceXMLRPCClient:
    def __init__(self, host='127.0.0.1', server_port = 8000, cli_port = 8001):
        self.server = ServerProxy("http://{}:{}".format(host, server_port))
        self.t = self.listen(cli_port)

    def listen(self, client_port):
        """Inicia el servidor RPC para recibir insultos"""

        def run_client_server():
            with SimpleXMLRPCServer(("127.0.0.1", client_port), allow_none=True, logRequests=False) as server_subs:
                server_subs.register_instance(self)
                server_subs.timeout = 5
                while getattr(threading.current_thread(), "do_run", True):
                    server_subs.handle_request()

        t = threading.Thread(target=run_client_server, daemon=True)
        t.do_run = True
        t.start()

        callback_url = f"http://127.0.0.1:{client_port}"
        if self.server.register_subscriber(callback_url):
            print("Successfully registered as subscriber")
        else:
            print("Registration failed")

        return t

    def add_insult(self, insult):
        self.server.add_insult(insult)

    def get_all_insults(self):
        return self.server.get_all_insults()

    def notify(self, insult: str):
        """Método llamado por el servidor para enviar insultos"""
        print(f"Received insult: {insult}")