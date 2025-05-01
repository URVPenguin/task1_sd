import threading
import time
from collections import defaultdict
from time import sleep

from multiprocessing import Process, Manager
from server_client import server_client
from functions import get_free_port, filter_work, service_work, measure_resources, plot_resources, plot_results, monitor_resources


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
        resource_data = {
            'cpu': [], 'ram': [],
            'disk_read': [], 'disk_write': [],
            'net_sent': [], 'net_recv': []
        }

        for client_count in client_counts:
            print(f"\nTesting with {client_count} clients...")

            manager = Manager()
            latencies = manager.list()

            measurements = defaultdict(list)
            measure_thread = threading.Thread(target=monitor_resources, args=[measurements], daemon=True)
            measure_thread.do_run = True
            measure_thread.start()

            processes = []
            for i in range(client_count):
                p = Process(target=client_work, args=([latencies, client_class, requests_per_client]))
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            measure_thread.do_run = False
            measure_thread.join()

            resource_data['cpu'].append(sum(measurements['cpu']) / len(measurements['cpu']) if len(measurements['cpu']) > 0 else 0)
            resource_data['ram'].append(sum(measurements['ram']) / len(measurements['ram']) if len(measurements['ram']) > 0 else 0)
            resource_data['disk_read'].append(sum(measurements['disk_read']) / len(measurements['disk_read']) if len(measurements['disk_read']) > 0 else 0)
            resource_data['disk_write'].append(sum(measurements['disk_write']) / len(measurements['disk_write']) if len(measurements['disk_write']) > 0 else 0)
            resource_data['net_sent'].append(sum(measurements['net_sent']) / len(measurements['net_sent']) if len(measurements['net_sent']) > 0 else 0)
            resource_data['net_recv'].append(sum(measurements['net_recv']) / len(measurements['net_recv']) if len(measurements['net_recv']) > 0 else 0)

            latencies = list(latencies)
            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")

        self.stop_server()
        plot_results(client_class, client_counts, results)
        plot_resources(client_class, client_counts, resource_data)

if __name__ == "__main__":
    for key, data in server_client.items():
        for idx, client in enumerate(data['clients']):
            print(f"Testing {key} using {client.__name__} (single node) ...")
            tester = SingleNodeStressTester(Process(target=data['targets'][idx]))
            tester.run_stress_test(client, max_clients=50, requests_per_client=50)