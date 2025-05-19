import time
from multiprocessing import Manager
from multiprocessing.pool import Pool
from pathlib import Path

from matplotlib import pyplot as plt

from clients.rabbitmq.insult_filter_client import InsultFilterRabbitMQClient
from servers.rabbitmq.insult_filter import run_server
from stress_tests.dynamic_scaler.rabbitmq_monitor import RabbitmqMonitor
from stress_tests.dynamic_scaler.dynamic_scaler import DynamicScaler
from stress_tests.dynamic_scaler.servers_manager import ServersManager
from stress_tests.test_utils.docker_container_manager import DockerContainerManager


def process_task(args):
    client_id, text, host, port, processing_time, lock, latencies = args
    client = InsultFilterRabbitMQClient(host, port)
    try:
        start_time = time.perf_counter()
        response = client.submit_text(text)
        duration = time.perf_counter() - start_time
        latencies.append(duration)
        with lock:
            if len(processing_time) >= 500:
                processing_time.pop(0)
            processing_time.append(duration)
        return client_id, text, response, duration
    except Exception as e:
        return client_id, text, str(e), 0
    finally:
        client.close()

class DynamicMultinodeTester:
    def __init__(self):
        self.servers_manager = ServersManager(run_server)
        self.rabbitmq_monitor = RabbitmqMonitor()
        self.dynamic_scaler = DynamicScaler(self.rabbitmq_monitor, self.servers_manager)
        self.manager = Manager()
        self.processing_time = self.manager.list()
        self.latencies = self.manager.list()
        self.lock = self.manager.Lock()
        self.test_stats = []

    def run_stress_test(self, test_data, host="127.0.0.1", port=5672):
        self.start_all(self.processing_time)

        for item in test_data:
            if len(item) == 2:
                clients,requests = item
                reps = 1
            else:
                clients, requests, reps = item

            for r in range(reps):
                tasks = []
                for i in range(requests):
                    client_id = i % clients
                    tasks.append((client_id, "Hola", host, port, self.processing_time, self.lock, self.latencies))

                start_time = time.perf_counter()
                with Pool(processes=clients) as pool:
                    pool.map(process_task, tasks)
                total_time = time.perf_counter() - start_time
                active_servers = self.servers_manager.get_statistics()
                latencies = list(self.latencies)
                if latencies and total_time > 0:
                    avg_latency = sum(latencies) / len(latencies)
                    throughput = len(latencies) / total_time
                else:
                    avg_latency = 0
                    throughput = 0

                self.test_stats.append({
                    "clients": clients,
                    "requests": requests,
                    "repetition": r,
                    "avg_latency": avg_latency,
                    "throughput": throughput,
                    "total_time": total_time,
                    "active_servers": active_servers
                })

                with self.lock:
                    self.latencies[:] = []

        self.stop_all()
        self.plot_stats()

    def stop_all(self):
        self.dynamic_scaler.stop_scaling()
        self.rabbitmq_monitor.stop()
        self.servers_manager.pop_all()

    def start_all(self, processing_time):
        self.servers_manager.push()
        self.rabbitmq_monitor.start(processing_time)
        self.dynamic_scaler.start_scaling()

    def plot_stats(self):
        labels = [f"{s['clients']}c-{s['requests']}r-{s['repetition']}" for s in self.test_stats]
        latencies = [s["avg_latency"] for s in self.test_stats]
        throughputs = [s["throughput"] for s in self.test_stats]
        total_times = [s["total_time"] for s in self.test_stats]
        active_servers = [s["active_servers"] for s in self.test_stats]

        x = range(len(self.test_stats))
        plt.figure(figsize=(20, 6))

        plt.subplot(2, 2, 1)
        plt.plot(x, latencies, color='skyblue', marker='o')
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.title("Avg Latency (s)")
        plt.grid(True)

        plt.subplot(2, 2, 2)
        plt.plot(x, throughputs, color='lightgreen', marker='o')
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.title("Throughput (req/s)")
        plt.grid(True)

        plt.subplot(2, 2, 3)
        plt.plot(x, total_times, color='salmon', marker='o')
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.title("Total Time (s)")
        plt.grid(True)

        plt.subplot(2, 2, 4)
        plt.plot(x, active_servers, color='mediumpurple', marker='o')
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.title("Active Servers")
        plt.grid(True)

        plt.tight_layout()
        path = Path(__file__).parent.parent.parent
        path = path / "plots/dynamic_node_tests/insult_filter"
        Path(path).mkdir(parents=True, exist_ok=True)
        plt.savefig(f"{path}/dynamic_node_test.png")

if __name__ == "__main__":
    node_manager = DockerContainerManager()
    node_manager.run_rabbitmq()
    test = DynamicMultinodeTester()
    test.run_stress_test([(10, 200), (10, 200), (100, 500),(100, 1000), (500, 10000), (500, 15000), (500, 5000), (100, 1000), (10, 200)])
    node_manager.stop_container('rabbitmq')