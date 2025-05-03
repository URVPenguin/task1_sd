import time
from itertools import cycle
from multiprocessing import Process, Manager
from pathlib import Path
import matplotlib.pyplot as plt

from stress_tests.test_utils.docker_container_manager import DockerContainerManager
from stress_tests.test_utils.server_client import server_client
from stress_tests.test_utils.functions import get_free_port, filter_work, service_work


class StaticMultiNodeStressTester:
    def __init__(self, server_target, client_class, servers):
        self.servers_process = []
        self.server_target = server_target
        self.server_cycle = None
        self.servers_data = servers
        self.client_class = client_class

    def start_servers(self, servers):
        """Inicia los servidores en un proceso separado"""
        for server in range(servers):
            data = self.servers_data[server]
            proc = Process(target=self.server_target,
                           args=([data['host'], data['port']] if 'port' in data else [data['host']]))
            self.servers_process.append(proc)
            proc.start()

        time.sleep(1)

    def stop_servers(self):
        """Detiene los servidores"""
        for proc in self.servers_process:
            proc.terminate()

    def get_next_server(self):
        return next(self.server_cycle)

    def run_stress_test(self, max_clients=50, requests_per_client=100, servers=1):
        """Ejecuta test completo incluyendo broadcasting"""
        client_counts = range(10, max_clients+1, 10)

        results = [
            {'throughput': [], 'latency': [], 'total_time': []},
            {'throughput': [], 'latency': [], 'total_time': []},
            {'throughput': [], 'latency': [], 'total_time': []}
        ]

        for i in range(1, servers+1):
            self.start_servers(i)
            self.server_cycle = cycle(self.servers_data[:i])

            for client_count in client_counts:
                print(f"\nTesting with {client_count} clients...")

                manager = Manager()
                latencies = manager.list()

                start_time = time.perf_counter()
                processes = []
                for _ in range(client_count):
                    p = Process(target=self.client_work, args=([latencies, self.client_class,
                                                           requests_per_client, self.get_next_server()]))
                    processes.append(p)
                    p.start()

                for p in processes:
                    p.join()

                total_time = time.perf_counter() - start_time

                if len(latencies) >= 1:
                    latencies = list(latencies)
                    throughput = len(latencies) / sum(latencies)
                    avg_latency = sum(latencies) / len(latencies)

                    results[i-1]['throughput'].append(throughput)
                    results[i-1]['latency'].append(avg_latency)
                    results[i-1]['total_time'].append(total_time)

                    print(f"  Throughput: {throughput:.2f} req/s")
                    print(f"  Avg latency: {avg_latency:.4f} s")
                    print(f"  Time: {total_time:.4f} s")

            self.stop_servers()
        self.plot_results(client_counts, results)

    def client_work(self, latencies, client_class, requests_per_client, server):
        try:
            client = None
            if client_class.__name__ == 'InsultServiceXMLRPCClient':
                client = client_class(server['host'], server['port'], get_free_port())
            elif 'port' not in server:
                client = client_class(server['host'])
            else:
                client = client_class(server['host'], server['port'])

            start = time.perf_counter()
            if 'InsultFilter' in client_class.__name__:
                filter_work(client, requests_per_client)
            else:
                service_work(client, requests_per_client)
            latencies.append(time.perf_counter() - start)
        except Exception as e:
            print(f"Error conn {e}")

    def plot_results(self, client_counts, results):
        plt.figure(figsize=(15, 15))

        # Gráfico de Throughput
        plt.subplot(2, 2, 1)
        for servers, data in enumerate(results):
            plt.plot(client_counts, data['throughput'], 'o-', label=f'{servers+1} servidores')
        plt.title("Throughput vs Número de Clientes")
        plt.xlabel("Clientes")
        plt.ylabel("Requests/sec")
        plt.legend()
        plt.grid(True)

        # Gráfico de Latencia
        plt.subplot(2, 2, 2)
        for servers, data in enumerate(results):
            plt.plot(client_counts, data['latency'], 'o-', label=f'{servers+1} servidores')
        plt.title("Latencia vs Número de Clientes")
        plt.xlabel("Clientes")
        plt.ylabel("Latencia (segundos)")
        plt.legend()
        plt.grid(True)

        # Gráfico de Tiempo Total
        plt.subplot(2, 2, 3)
        for servers, data in enumerate(results):
            plt.plot(client_counts, data['total_time'], 'o-', label=f'{servers+1} servidores')
        plt.title("Tiempo Total vs Número de Clientes")
        plt.xlabel("Clientes")
        plt.ylabel("Tiempo (segundos)")
        plt.legend()
        plt.grid(True)

        plt.subplot(2, 2, 4)
        if len(results) > 1:
            base_time = results[0]['total_time']
            for servers, data in enumerate(results[1:], start=1):  # Empezamos desde el segundo servidor
                speedup = [single / multi for single, multi in zip(base_time, data['total_time'])]
                line = plt.plot(client_counts, speedup, 'o-', label=f'Speedup {servers + 1} servidores')
                for x, y in zip(client_counts, speedup):
                    plt.annotate(
                        f"{y:.2f}x",
                        (x, y),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center',
                        va='bottom',
                        color=line[0].get_color(),
                        bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2'),
                        fontsize=8
                    )
            plt.title("Speedup vs Número de Clientes")
            plt.xlabel("Clientes")
            plt.ylabel("Speedup (Tiempo 1 servidor / Tiempo N servidores)")
            plt.axhline(y=1, color='gray', linestyle='--')  # Línea de referencia
            plt.legend()
            plt.grid(True)

        plt.tight_layout()
        path = Path(__file__).parent.parent.parent
        path = path / "plots/multinode_node_tests/"
        path = path / "insult_filter" if 'InsultFilter' in self.client_class.__name__ else path / "insult_service"
        Path(path).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{path}/multinode_node_test_{self.client_class.__name__}.png")

def stop_all_containers(servers):
    for server in servers:
        if 'container_name' in server:
            manager.stop_container(server['container_name'])

def start_all_containers(tecnology, servers):
    for server in servers:
        if 'container_name' in server:
            if tecnology == 'redis':
                manager.run_redis(server['container_name'], server['port'], server['host'], True)
            elif tecnology == 'pyro':
                manager.run_pyro_nameserver(container_name=server['container_name'], restart_existing=True)
            elif tecnology == 'rabbitMQ':
                manager.run_rabbitmq(server['container_name'], server['port'], server['host'], True)


if __name__ == "__main__":
    manager = DockerContainerManager()

    for key, data in server_client.items():
        stop_all_containers(data['servers'])
        start_all_containers(key, data['servers'])

        for idx, client in enumerate(data['clients']):
           tester = StaticMultiNodeStressTester(data['targets'][idx], client, data['servers'])
           print(f"Testing {key} using {client.__name__} (static multinode node) ...")
           tester.run_stress_test(max_clients=50, requests_per_client=50, servers=3)

        stop_all_containers(data['servers'])


