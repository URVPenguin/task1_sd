import threading
import time
import matplotlib.pyplot as plt
from multiprocessing import Process

from clients.pyro.insult_filter_client import InsultFilterPyroClient
from clients.redis.insult_filter_client import InsultFilterRedisClient
from clients.xmlrpc.insult_filter_client import InsultFilterXMLRPClient
from servers.xmlrpc.insult_filter import run_server as xmlrpc_run_server
from servers.redis.insult_filter import run_server as redis_run_server
from servers.pyro.insult_filter import run_server as pyro_run_server


def plot_results(client_class, client_counts, results):
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
    plt.savefig(f"single_stress_test_{client_class.__name__}.png")


class SingleNodeStressTesterFilterService:
    def __init__(self, process):
        self.server_process = process

    def start_server(self):
        """Inicia el servidor en un proceso separado"""
        self.server_process.start()
        time.sleep(1)

    def stop_server(self):
        """Detiene el servidor"""
        self.server_process.terminate()

    def run_stress_test(self, client_class, max_clients=50, requests_per_client=100):
        """Ejecuta test completo incluyendo broadcasting"""
        self.start_server()

        client_counts = range(0, max_clients+1, 10)
        results = { 'throughput': [], 'latency': []}

        for client_count in client_counts:
            print(f"\nTesting with {client_count} clients...")

            latencies = []
            def client_work():
                try:
                    client = client_class()
                    start = time.perf_counter()
                    for _ in range(requests_per_client):
                        if _ % 2 == 0:
                            client.submit_text("insult idiot retardet")
                        else:
                            client.get_results()
                    latencies.append(time.perf_counter() - start)
                except Exception as e:
                    print(f"Error conn {e} > {client}")

            # Ejecutar clientes en paralelo


            # procs = []
            # for cli in range(client_count):
            #     proc =Process(target=client_work, daemon=True, name=f"client_{cli}" )
            #     procs.append(proc)
            #     proc.start()
            #
            # for proc in procs:
            #     proc.
            #     proc.join()

            t = []
            for cli in range(client_count):
                a = threading.Thread(target=client_work)
                t.append(a)
                a.start()
            for a in t:
                a.join()

            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")

        self.stop_server()
        plot_results(client_class, client_counts, results)

if __name__ == "__main__":
    print("Testing xmlrpc insult filter (single node) ...")
    tester = SingleNodeStressTesterFilterService(Process(target=xmlrpc_run_server))
    tester.run_stress_test(InsultFilterXMLRPClient, max_clients=40, requests_per_client=70)

    print("Testing Redis insult filter (single node) ...")
    tester = SingleNodeStressTesterFilterService(Process(target=redis_run_server))
    tester.run_stress_test(InsultFilterRedisClient, max_clients=50, requests_per_client=50)

    print("Testing Pyro insult filter (single node) ...")
    tester = SingleNodeStressTesterFilterService(Process(target=pyro_run_server))
    tester.run_stress_test(InsultFilterPyroClient, max_clients=50, requests_per_client=50)
