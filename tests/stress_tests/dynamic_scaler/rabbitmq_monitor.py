import time
from multiprocessing import Manager, Process, Event

import requests
from requests import RequestException

from stress_tests.dynamic_scaler.interface.Monitor import Monitor

class RabbitmqMonitor(Monitor):
    def __init__(self, host="localhost", port=15672, user="guest", password="guest"):
        self.base_url = f"http://{host}:{port}/api"
        self.auth = (user, password)
        self.queues = ["submit_text_queue"]
        self.manager = Manager()
        self.metrics = self.manager.dict()
        self.lock_metric = self.manager.Lock()
        self.stop_event = self.manager.Event()
        self.response_time = 1
        self.update_process = None
        self.session = requests.Session()

    def start(self, processing_time):
        """Inicia el hilo de actualización de métricas"""
        if self.update_process is None or not self.update_process.is_alive():
            self.stop_event.clear()
            self.update_process = Process(
                target=self.update_metrics,
                args=(processing_time,),
                daemon=False
            )
            self.update_process.start()

    def stop(self):
        """Detiene el hilo de actualización"""
        if self.update_process and self.update_process.is_alive():
            self.stop_event.set()
            self.update_process.join(timeout=3)
            if self.update_process.is_alive():
                self.update_process.terminate()
                self.update_process.join()
            self.update_process = None

    def update_metrics(self, processing_time):
        try:
            while not self.stop_event.is_set():
                try:
                    new_metrics = self.request_metrics(processing_time)
                    if new_metrics:
                        with self.lock_metric:
                            self.metrics.update(new_metrics)
                except RequestException as e:
                    print(f"HTTP Error: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
                time.sleep(0.1)
        finally:
            self.session.close()

    def request_metrics(self, processing_time):
        """Obtiene métricas con cálculos robustos"""
        metrics = {
            "arrival_rate": 0.0,
            "target_response_time": self.response_time,
            "processing_time": self.get_avg_processing_time(processing_time),
            "pending_messages": 0,
        }

        for queue in self.queues:
            queue_data = self.get_queue_metrics(queue)

            metrics["pending_messages"] += queue_data.get("messages_ready", 0)
            stats = queue_data.get("message_stats", {})
            metrics["arrival_rate"] += stats.get("publish_details", {}).get("rate", 0)

        return metrics

    def get_metrics(self):
        with self.lock_metric:
            return dict(self.metrics)

    def get_avg_processing_time(self, processing_time):
        with self.lock_metric:
            if not processing_time:
                return 1.0
            return sum(processing_time) / len(processing_time)

    def get_queue_metrics(self, queue_name: str):
        """Obtiene métricas específicas de una cola replicada"""
        try:
            url = f"{self.base_url}/queues/%2F/{queue_name}"
            response = self.session.get(url, auth=self.auth, timeout=1)
            data = response.json()
            return data
        except requests.RequestException as e:
            print(f"Error obteniendo métricas: {e}")
            return {}