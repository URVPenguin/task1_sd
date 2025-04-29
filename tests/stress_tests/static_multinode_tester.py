import time
import random
import threading
from xmlrpc.server import SimpleXMLRPCServer

import matplotlib.pyplot as plt
from xmlrpc.client import ServerProxy
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from servers.xmlrpc.insult_service import run_server

class MultiServerStressTester:
    def __init__(self):
        self.server_processes = []
        self.subscriber_threads = []
        self.received_counts = defaultdict(int)
        self.latencies = []

    def start_servers(self, num_servers):
        """Inicia múltiples servidores en puertos consecutivos"""
        base_port = 8000
        for i in range(num_servers):
            port = base_port + i
            p = Process(target=run_server, kwargs={'port': port})
            p.start()
            self.server_processes.append(p)
        time.sleep(2)  # Esperar que todos los servidores inicien

    def stop_servers(self):
        """Detiene todos los servidores"""
        for p in self.server_processes:
            p.terminate()
        self.server_processes = []

    def run_stress_test(self, max_servers=3, clients_per_server=20, requests_per_client=100, duration=30):
        """Ejecuta test con diferentes configuraciones de servidores"""
        results = {
            'throughput': [],
            'latency': [],
            'broadcast_received': [],
            'speedup': []
        }

        server_counts = range(1, max_servers + 1)
        base_time = None

        for num_servers in server_counts:
            print(f"\n=== Testing with {num_servers} servers ===")

            # Iniciar servidores
            self.start_servers(num_servers)

            # Preparar lista de servidores disponibles
            server_ports = [8000 + i for i in range(num_servers)]

            # Iniciar test
            start_time = time.perf_counter()
            self._start_subscribers(clients_per_server * num_servers, server_ports)

            # Distribuir carga entre servidores
            total_clients = clients_per_server * num_servers
            with ThreadPoolExecutor(max_workers=total_clients) as executor:
                executor.map(self._client_work,
                             [random.choice(server_ports) for _ in range(total_clients)],
                             [requests_per_client] * total_clients)

            # Esperar periodo de broadcasting
            time.sleep(duration)

            # Calcular métricas
            total_time = time.perf_counter() - start_time
            total_requests = total_clients * requests_per_client
            throughput = total_requests / total_time
            avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)
            results['broadcast_received'].append(sum(self.received_counts.values()))

            # Calcular speedup (si es al menos el segundo test)
            if num_servers == 1:
                base_time = total_time
                results['speedup'].append(1.0)
            else:
                results['speedup'].append(base_time / total_time)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")
            print(f"  Broadcasts received: {sum(self.received_counts.values())}")
            print(f"  Speedup: {results['speedup'][-1]:.2f}x")

            # Limpiar para siguiente iteración
            self._stop_subscribers()
            self.stop_servers()
            self.latencies = []
            self.received_counts = defaultdict(int)

        self._plot_results(server_counts, results)

    def _client_work(self, server_port, requests):
        """Ejecuta el trabajo de un cliente contra un servidor específico"""
        server = ServerProxy(f"http://localhost:{server_port}")
        for _ in range(requests):
            start = time.perf_counter()

            # Operación aleatoria
            op = random.randint(0, 2)
            if op == 0:
                server.add_insult(f"stress_{server_port}_{time.time()}")
            elif op == 1:
                server.get_all_insults()
            else:
                client_id = threading.get_ident()
                server.register_subscriber(f"http://localhost:{9000 + client_id}")

            self.latencies.append(time.perf_counter() - start)

    def _start_subscribers(self, num_subscribers, server_ports):
        """Inicia clientes que reciben broadcasts de todos los servidores"""
        self.subscriber_threads = []

        def subscriber_loop(client_id):
            port = 9000 + client_id
            with SimpleXMLRPCServer(("localhost", port)) as server_subs:
                server_subs.register_instance(self)
                server_subs.timeout = 1
                current_thread = threading.current_thread()
                while getattr(current_thread, "do_run", True):
                    server_subs.handle_request()

        for i in range(num_subscribers):
            t = threading.Thread(target=subscriber_loop, args=(i,))
            t.do_run = True
            t.daemon = True
            t.start()
            self.subscriber_threads.append(t)

            # Registrar en un servidor aleatorio
            server = ServerProxy(f"http://localhost:{random.choice(server_ports)}")
            server.register_subscriber(f"http://localhost:{9000 + i}")

    def _stop_subscribers(self):
        """Detiene todos los subscriptores"""
        for t in self.subscriber_threads:
            t.do_run = False
            t.join()
        self.subscriber_threads = []

    def notify(self, insult):
        """Método llamado por los servidores para enviar insultos"""
        client_id = threading.current_thread().ident
        self.received_counts[client_id] += 1
        return True

    def _plot_results(self, server_counts, results):
        """Genera gráficos con los resultados"""
        plt.figure(figsize=(15, 10))

        # Throughput
        plt.subplot(2, 2, 1)
        plt.plot(server_counts, results['throughput'], 'b-o')
        plt.title("Throughput vs Number of Servers")
        plt.xlabel("Number of Servers")
        plt.ylabel("Requests per Second")
        plt.grid(True)

        # Latency
        plt.subplot(2, 2, 2)
        plt.plot(server_counts, results['latency'], 'r-o')
        plt.title("Latency vs Number of Servers")
        plt.xlabel("Number of Servers")
        plt.ylabel("Average Latency (s)")
        plt.grid(True)

        # Broadcasts
        plt.subplot(2, 2, 3)
        plt.plot(server_counts, results['broadcast_received'], 'g-o')
        plt.title("Broadcasts Received vs Number of Servers")
        plt.xlabel("Number of Servers")
        plt.ylabel("Total Broadcasts Received")
        plt.grid(True)

        # Speedup
        plt.subplot(2, 2, 4)
        plt.plot(server_counts, results['speedup'], 'c-s')
        plt.title("Speedup vs Number of Servers")
        plt.xlabel("Number of Servers")
        plt.ylabel("Speedup (T1/TN)")
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("multi_server_stress_test.png")
        plt.show()


if __name__ == "__main__":
    tester = MultiServerStressTester()
    tester.run_stress_test(
        max_servers=3,  # Probar con 1, 2 y 3 servidores
        clients_per_server=30,  # 30 clientes por servidor
        requests_per_client=200,  # 200 peticiones por cliente
        duration=20  # 20 segundos de test de broadcasting
    )