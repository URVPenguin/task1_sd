import socket
from pathlib import Path
import time
from time import sleep

import matplotlib.pyplot as plt
from multiprocessing import Process, Manager

from clients.pyro.insult_service_client import InsultServicePyroClient
from clients.redis.insult_service_client import InsultServiceRedisClient
from clients.xmlrpc.insult_service_client import InsultServiceXMLRPCClient
from clients.pyro.insult_filter_client import InsultFilterPyroClient
from clients.redis.insult_filter_client import InsultFilterRedisClient
from clients.xmlrpc.insult_filter_client import InsultFilterXMLRPClient
from clients.rabbitmq.insult_filter_client import InsultFilterRabbitMQClient
from clients.rabbitmq.insult_service_client import InsultServiceRabbitMQClient
from servers.xmlrpc.insult_service import run_server as serv_xmlrpc_run_server
from servers.redis.insult_service import run_server as serv_redis_run_server
from servers.pyro.insult_service import run_server as serv_pyro_run_server
from servers.rabbitmq.insult_service import run_server as serv_rabbitmq_run_server
from servers.xmlrpc.insult_filter import run_server as filt_xmlrpc_run_server
from servers.redis.insult_filter import run_server as filt_redis_run_server
from servers.pyro.insult_filter import run_server as filt_pyro_run_server
from servers.rabbitmq.insult_filter import run_server as filt_rabbitmq_run_server


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

def get_free_port():
    """Encuentra y devuelve un puerto TCP disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def service_work(client, requests_per_client):
    for i in range(requests_per_client):
        if i % 2 == 0:
            client.add_insult(f"insult{i}")
        else:
            client.get_all_insults()

def filter_work(client, requests_per_client):
    for i in range(requests_per_client):
        if i % 2 == 0:
            client.submit_text("insult idiot retardet")
        else:
            client.get_results()

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
    clients = {
        "xmlrpc": {
            "targets": [serv_xmlrpc_run_server, filt_xmlrpc_run_server],
            "clients": [InsultServiceXMLRPCClient, InsultFilterXMLRPClient]
        },
        "redis": {
            "targets": [serv_redis_run_server, filt_redis_run_server],
            "clients": [InsultServiceRedisClient, InsultFilterRedisClient]
        },
        "pyro": {
            "targets": [serv_pyro_run_server, filt_pyro_run_server],
            "clients": [InsultServicePyroClient, InsultFilterPyroClient]
        },
        "rabbitMQ": {
            "targets": [serv_rabbitmq_run_server, filt_rabbitmq_run_server],
            "clients": [InsultServiceRabbitMQClient, InsultFilterRabbitMQClient]
        }
    }

    for key, data in clients.items():
        for idx, client in enumerate(data['clients']):
            print(f"Testing {key} using {client.__name__} (single node) ...")
            tester = SingleNodeStressTester(Process(target=data['targets'][idx]))
            tester.run_stress_test(client, max_clients=50, requests_per_client=50)