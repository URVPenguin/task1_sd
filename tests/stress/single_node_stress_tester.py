import random
import threading
import time
import inspect
from concurrent.futures.thread import ThreadPoolExecutor
from xmlrpc.server import SimpleXMLRPCServer
import matplotlib.pyplot as plt
from xmlrpc.client import ServerProxy
from multiprocessing import Process

from clients.xmlrpc.insult_service_client import InsultServiceXMLRPCClient
from servers.xmlrpc.insult_service import run_server


class SingleNodeStressTester:
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

    def run_stress_test(self, max_clients=50, requests_per_client=100):
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
        }

        for client_count in client_counts:
            print(f"\nTesting with {client_count} clients...")

            # Preparar clientes RPC
            clients = [InsultServiceXMLRPCClient("http://localhost:8000") for _ in range(client_count)]

            self._start_subscribers(clients)

            latencies = []

            def client_work(client_idx, client):
                for _ in range(requests_per_client):
                    start = time.perf_counter()  # Más preciso

                    op = random.randint(0, 3)
                    if op == 0:
                        client.server.add_insult(f"stress_{client_idx}_{time.time()}")
                    else:
                        client.server.get_all_insults()

                    latencies.append(time.perf_counter() - start)

            # Ejecutar clientes en paralelo
            with ThreadPoolExecutor(max_workers=client_count) as executor:
                executor.map(client_work, range(client_count), clients)

            # Esperar un periodo para recibir broadcasts
            time.sleep(5)

            # Calcular métricas
            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")

            # Limpiar subscriptores
            self._stop_subscribers()

        self.stop_server()
        self._plot_results(client_counts, results)

    def _start_subscribers(self, clients):
        """Inicia clientes que reciben broadcasts"""
        for i, client in enumerate(clients):
            self.subscriber_threads.append(client.listen(8001 + i))

    def _stop_subscribers(self):
        """Detiene los clientes subscriptores"""
        for t in self.subscriber_threads:
            t.join()
        self.subscriber_threads = []


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

        plt.tight_layout()
        plt.savefig("complete_stress_test.png")
        plt.show()


if __name__ == "__main__":
    tester = SingleNodeStressTester()
    tester.run_stress_test(
        max_clients=10,
        requests_per_client=20,
    )