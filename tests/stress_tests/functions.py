import socket
import threading
import time
from pathlib import Path

import psutil
from matplotlib import pyplot as plt

def get_free_port():
    """Encuentra y devuelve un puerto TCP disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def measure_resources(duration_sec=1):
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


def monitor_resources(measures, interval=0.1):
    t = threading.current_thread()
    disk = psutil.disk_io_counters()
    net = psutil.net_io_counters()
    last_disk = {'disk_read': disk.read_bytes,'disk_write': disk.write_bytes }
    last_net = {'net_sent': net.bytes_sent, 'net_recv': net.bytes_recv}
    while getattr(t, "do_run", True):
        new_measure = measure_resources()
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

def plot_resources(client_class, client_counts, resource_data):
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
    path = path / "plots/single_node_tests/insult_filter/resources" if 'InsultFilter' in client_class.__name__ else path / "plots/single_node_tests/insult_service/resources"
    Path(path).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{path}/resources_single_node_test_{client_class.__name__}.png")

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