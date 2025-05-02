import threading
import time
from collections import defaultdict
from multiprocessing import Process, Manager
from pathlib import Path

import psutil
from matplotlib import pyplot as plt

from test_utils.docker_container_manager import DockerContainerManager
from test_utils.server_client import server_client
from test_utils.functions import get_free_port, filter_work, service_work

class SingleNodeStressTester:
    def __init__(self, process, client_class):
        self.server_process = process
        self.client_class = client_class

    def start_server(self):
        """Inicia el servidor en un proceso separado"""
        self.server_process.start()
        time.sleep(1)

    def stop_server(self):
        """Detiene el servidor"""
        self.server_process.terminate()

    def run_stress_test(self, max_clients=50, requests_per_client=100):
        """Ejecuta test completo incluyendo broadcasting"""
        self.start_server()

        client_counts = range(10, max_clients+1, 10)
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
            measure_thread = threading.Thread(target=self.monitor_resources, args=[measurements], daemon=True)
            measure_thread.do_run = True
            measure_thread.start()

            processes = []
            for i in range(client_count):
                p = Process(target=self.client_work, args=([latencies, self.client_class, requests_per_client]))
                processes.append(p)
                p.start()

            for p in processes:
                p.join()

            measure_thread.do_run = False
            measure_thread.join()

            for k in measurements:
                resource_data[k].append(sum(measurements[k]) / len(measurements[k])if measurements[k] else 0)

            latencies = list(latencies)
            throughput = len(latencies) / sum(latencies) if latencies else 0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0

            results['throughput'].append(throughput)
            results['latency'].append(avg_latency)

            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg latency: {avg_latency:.4f} s")

        self.stop_server()
        self.plot_results(client_counts, results)
        self.plot_resources(client_counts, resource_data)

    def client_work(self, latencies, client_class, requests_per_client):
        try:
            client = client_class(
                cli_port=get_free_port()) if client_class.__name__ == 'InsultServiceXMLRPCClient' else client_class()
            start = time.perf_counter()
            if 'InsultFilter' in client_class.__name__:
                filter_work(client, requests_per_client)
            else:
                service_work(client, requests_per_client)
            latencies.append(time.perf_counter() - start)
        except Exception as e:
            print(f"Error conn {e}")

    def plot_resources(self, client_counts, resource_data):
        """Genera gráficos de uso de recursos."""
        plt.figure(figsize=(15, 10))

        # CPU
        plt.subplot(2, 2, 1)
        plt.plot(client_counts, resource_data['cpu'], 'm-^')
        plt.title("CPU Usage (%) vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("CPU %")
        plt.grid(True)

        # RAM
        plt.subplot(2, 2, 2)
        plt.plot(client_counts, resource_data['ram'], 'c-s')
        plt.title("RAM Usage (%) vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("RAM %")
        plt.grid(True)

        # Red (Tráfico de red)
        plt.subplot(2, 2, 3)
        plt.plot(client_counts, resource_data['net_sent'], 'r-', label="MB Sent")
        plt.plot(client_counts, resource_data['net_recv'], 'b-', label="MB Received")
        plt.title("Network Traffic vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("MB")
        plt.legend()
        plt.grid(True)

        # Disco
        plt.subplot(2, 2, 4)
        plt.plot(client_counts, resource_data['disk_read'], 'y-.', label="Read")
        plt.plot(client_counts, resource_data['disk_write'], 'r-.', label="Write")
        plt.title("Disk IO vs Clients")
        plt.xlabel("Number of Clients")
        plt.ylabel("Bytes")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        path = Path(__file__).parent.parent.parent
        path = path / "plots/single_node_tests/insult_filter/resources" \
            if 'InsultFilter' in self.client_class.__name__ \
            else path / "plots/single_node_tests/insult_service/resources"
        Path(path).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{path}/resources_single_node_test_{self.client_class.__name__}.png")

    def plot_results(self, client_counts, results):
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
        path = path / "plots/single_node_tests/insult_filter" \
            if 'InsultFilter' in self.client_class.__name__ else path / "plots/single_node_tests/insult_service"
        Path(path).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{path}/single_node_test_{self.client_class.__name__}.png")

    def measure_resources(self, duration_sec=1):
        """Mide CPU, RAM, disco y red durante un período."""
        cpu_percent = psutil.cpu_percent(interval=duration_sec)
        ram = psutil.virtual_memory().percent
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        return {
            'cpu': cpu_percent,
            'ram': ram,
            'disk_read': disk_io.read_bytes,
            'disk_write': disk_io.write_bytes,
            'net_sent': net_io.bytes_sent,
            'net_recv': net_io.bytes_recv,
        }

    def monitor_resources(self, measures, interval=0.1):
        t = threading.current_thread()
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()
        last_disk = {'disk_read': disk.read_bytes, 'disk_write': disk.write_bytes}
        last_net = {'net_sent': net.bytes_sent, 'net_recv': net.bytes_recv}
        while getattr(t, "do_run", True):
            new_measure = self.measure_resources()
            for key, value in new_measure.items():
                if key in ['cpu', 'ram']:
                    measures[key].append(value)

            measures['disk_read'].append(new_measure['disk_read'] - last_disk['disk_read'])
            measures['disk_write'].append(new_measure['disk_write'] - last_disk['disk_write'])
            measures['net_sent'].append((new_measure['net_sent'] - last_net['net_sent']) / (1024 * 1024))
            measures['net_recv'].append((new_measure['net_recv'] - last_net['net_recv']) / (1024 * 1024))

            last_disk = {'disk_read': new_measure['disk_read'], 'disk_write': new_measure['disk_write']}
            last_net = {'net_sent': new_measure['net_sent'], 'net_recv': new_measure['net_recv']}

            time.sleep(interval)

def stop_containers():
    manager = DockerContainerManager()
    for container in ['rabbitmq', 'redis', 'pyro-ns']:
        manager.stop_container(container)

def start_containers():
    manager = DockerContainerManager()
    manager.run_rabbitmq()
    manager.run_redis()
    manager.run_pyro_nameserver()

if __name__ == "__main__":
    stop_containers()
    start_containers()

    for key, data in server_client.items():
        for idx, client in enumerate(data['clients']):
            print(f"Testing {key} using {client.__name__} (single node) ...")
            tester = SingleNodeStressTester(Process(target=data['targets'][idx]), client)
            tester.run_stress_test(max_clients=50, requests_per_client=50)

    stop_containers()