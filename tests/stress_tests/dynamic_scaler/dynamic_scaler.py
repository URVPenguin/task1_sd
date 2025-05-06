import math
import time
from multiprocessing import Process, Event

from stress_tests.dynamic_scaler.interface import Monitor
from stress_tests.dynamic_scaler.servers_manager import ServersManager

class DynamicScaler:
    def __init__(self, monitor: Monitor, servers_manager: ServersManager):
        self.monitor = monitor
        self.servers_manager = servers_manager
        self.scaling_process = None
        self.max_workers = 15
        self.stop_event = Event()

    def start_scaling(self):
        if self.scaling_process is None or not self.scaling_process.is_alive():
            self.stop_event.clear()
            self.scaling_process = Process(
                target=self.monitor_and_scale_loop,
                daemon=False
            )
            self.scaling_process.start()

    def stop_scaling(self):
        """Detiene el proceso de forma segura"""
        if self.scaling_process and self.scaling_process.is_alive():
            self.stop_event.set()
            self.scaling_process.join(timeout=3)
            if self.scaling_process.is_alive():
                self.scaling_process.terminate()
                self.scaling_process.join()
            self.scaling_process = None

    def monitor_and_scale_loop(self):
        """Bucle principal para el proceso de escalado"""
        while not self.stop_event.is_set():
            try:
                self.monitor_and_scale()
            except Exception as e:
                print(f"Error en escalado: {e}")
            time.sleep(5)

    def monitor_and_scale(self):
        """Monitoriza y escala el cluster"""
        metrics = self.monitor.get_metrics()
        #
        # lambda_ = metrics["arrival_rate"]  # λ: Tasa de llegada (msg/seg)
        # T = metrics["processing_time"]  # T: Tiempo procesamiento (seg/msg)
        # C = 1 / T if T > 0 else 1  # C: Capacidad worker (msg/seg) = 1/T
        #
        # N = (lambda_ * T) / C
        # required_workers = max(1, math.ceil(N))
        #
        # print(required_workers, lambda_ ,T, C, N)
        #
        #
        if metrics:
            required_workers = self.calculate_required_workers(metrics)
            current_workers = self.servers_manager.count()
            self.scale(current_workers, required_workers)

    def calculate_required_workers(self, metrics):
        B = metrics["pending_messages"]
        lam = metrics["arrival_rate"]
        C = 1 / metrics["processing_time"] if metrics["processing_time"] > 0 else 1

        N = math.ceil((B + (lam * metrics["target_response_time"])) / C)
        print(f"N: {N}, {metrics}, calc:{(B + (lam * metrics["target_response_time"])) / C}")
        return max(min(N, self.max_workers), 1)

    def scale(self, current: int, required: int):
        if required > current:
            delta = required - current
            print(f"[ESCALANDO] Requeridos: {required}, Actuales: {current} -> Añadiendo {delta} workers")
            for _ in range(delta):
                self.servers_manager.push()
        elif required < current:
            delta = current - required
            print(f"[REDUCIENDO] Requeridos: {required}, Actuales: {current} -> Eliminando {delta} workers")
            for _ in range(delta):
                self.servers_manager.pop()