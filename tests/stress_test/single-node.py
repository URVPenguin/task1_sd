import random
import threading
import time
import inspect
from concurrent.futures.thread import ThreadPoolExecutor
from xmlrpc.server import SimpleXMLRPCServer

import matplotlib.pyplot as plt
from xmlrpc.client import ServerProxy
from multiprocessing import Process
from servers.xmlrpc.insult_service import run_server


class StressTester:
    def __init__(self):
        self.server_process = None
        self.subscriber_threads = []
        self.received_counts = []

    def start_server(self):
        """Inicia el servidor en un proceso separado"""
        self.server_process = Process(target=run_server)
        self.server_process.start()
        time.sleep(1)  # Esperar inicio del servidor

    def stop_server(self):
        """Detiene el servidor"""
        if self.server_process:
            self.server_process.terminate()

    def run_stress_test(self, max_clients=50, requests_per_client=100, duration=60):
        """Ejecuta test completo incluyendo broadcasting"""
        self.start_server()
        server = ServerProxy("http://localhost:8000")

        # Añadir insultos iniciales
        for i in range(100):
            server.add_insult(f"init_insult_{i}")

        # Configuración de tests
        client_counts = range(1, max_clients + 1, 10)
        results = {
            'throughput': [],
            'latency': [],
            'broadcast_received': []
        }

        for client_count in client_counts:
            print(f"\nTesting with {client_count} clients...")

            # Preparar clientes RPC
            clients = [ServerProxy("http://localhost:8000") for _ in range(client_count)]

            # Preparar subscriptores para broadcasting
            self.received_counts = [0] * client_count
            self._start_subscribers(client_count)

            latencies = []

            def client_work(client_idx):
                client = ServerProxy("http://localhost:8000")
                for _ in range(requests_per_client):
                    start = time.perf_counter()  # Más preciso

                    op = random.randint(0, 1)
                    if op == 0:
                        client.add_insult(f"stress_{client_idx}_{time.time()}")
                    else:
                        client.get_all_insults()

                    latencies.append(time.perf_counter() - start)

            # Ejecutar clientes en paralelo
            with ThreadPoolExecutor(max_workers=client_count) as executor:
                executor.map(client_work, range(client_count))

            # Esperar un periodo para recibir broadcasts
            time.sleep(5)

            # Calcular métricas
            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)
            results['broadcast_received'].append(sum(self.received_counts))

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")
            print(f"  Broadcasts received: {sum(self.received_counts)}")

            # Limpiar subscriptores
            self._stop_subscribers()

        self.stop_server()
        self._plot_results(client_counts, results)

    def _start_subscribers(self, count):
        """Inicia clientes que reciben broadcasts"""
        self.subscriber_threads = []
        self.received_counts = [0] * count

        def subscriber_loop(index):
            port = 8001 + index
            with SimpleXMLRPCServer(("localhost", port)) as server_subs:
                server_subs.register_instance(self)
                server_subs.timeout = 1
                current_thread = threading.current_thread()
                while getattr(current_thread, "do_run", True):
                    server_subs.handle_request()

        for i in range(count):
            t = threading.Thread(target=subscriber_loop, args=(i,))
            t.do_run = True
            t.daemon = True
            t.start()
            self.subscriber_threads.append(t)

            server = ServerProxy("http://localhost:8000")
            server.register_subscriber(f"http://localhost:{8001 + i}")

    def _stop_subscribers(self):
        """Detiene los clientes subscriptores"""
        for t in self.subscriber_threads:
            t.do_run = False
            t.join()
        self.subscriber_threads = []

    def notify(self, insult):
        """Método llamado por el servidor para enviar insultos"""
        port = inspect.currentframe().f_back.f_locals['self'].server_address[1]
        idx = port - 8001
        if 0 <= idx < len(self.received_counts):
            self.received_counts[idx] += 1
        return True

    def _plot_results(self, client_counts, results):
        """Genera gráficos con los resultados"""
        plt.figure(figsize=(15, 5))

        # Throughput
        plt.subplot(1, 3, 1)
        plt.plot(client_counts, results['throughput'], 'b-o')
        plt.title("Throughput vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("Requests per Second")
        plt.grid(True)

        # Latency
        plt.subplot(1, 3, 2)
        plt.plot(client_counts, results['latency'], 'r-o')
        plt.title("Latency vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("Average Latency (s)")
        plt.grid(True)

        # Broadcasts
        plt.subplot(1, 3, 3)
        plt.plot(client_counts, results['broadcast_received'], 'g-o')
        plt.title("Broadcasts Received vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("Total Broadcasts Received")
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("complete_stress_test.png")
        plt.show()


if __name__ == "__main__":
    tester = StressTester()
    tester.run_stress_test(
        max_clients=30,
        requests_per_client=200,
        duration=30
    )