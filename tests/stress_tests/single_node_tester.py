import socket
from pathlib import Path
import time
from time import sleep

import matplotlib.pyplot as plt
from multiprocessing import Process, Manager
from server_client import server_client
from functions import get_free_port, filter_work, service_work

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
    path = Path(__file__).parent.parent.parent
    path =  path / "plots/single_node_tests/insult_filter" if 'InsultFilter' in client_class.__name__ else path / "plots/single_node_tests/insult_service"
    Path(path).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{path}/single_node_test_{client_class.__name__}.png")

def client_work(latencies, client_class, requests_per_client):
    try:
        client = client_class(port=get_free_port()) if client_class.__name__ == 'InsultServiceXMLRPCClient' else client_class()
        start = time.perf_counter()
        if 'InsultFilter' in client_class.__name__:
            filter_work(client, requests_per_client)
        else:
            service_work(client, requests_per_client)
        latencies.append(time.perf_counter() - start)

        if 'InsultService' in client_class.__name__:
            sleep(5) #wait for broadcasting
    except Exception as e:
        print(f"Error conn {e}")

class SingleNodeStressTester:
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

            manager = Manager()
            latencies = manager.list()

            processes = []
            for i in range(client_count):
                p = Process(target=client_work, args=([latencies, client_class, requests_per_client]))
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            latencies = list(latencies)
            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")

        self.stop_server()
        plot_results(client_class, client_counts, results)

if __name__ == "__main__":
    for key, data in server_client.items():
        for idx, client in enumerate(data['clients']):
            print(f"Testing {key} using {client.__name__} (single node) ...")
            tester = SingleNodeStressTester(Process(target=data['targets'][idx]))
            tester.run_stress_test(client, max_clients=50, requests_per_client=50)