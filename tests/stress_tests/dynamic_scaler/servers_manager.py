import math
import multiprocessing
from multiprocessing import Process

import psutil

class ServersManager:
    def __init__(self, server_target):
        self.manager = multiprocessing.Manager()
        self.server_pids = self.manager.list()
        self.server_target = server_target
        self.lock = self.manager.Lock()
        self.active_servers = self.manager.list()

    def push(self):
        process = Process(target=self.server_target, daemon=False)
        process.start()
        with self.lock:
            self.server_pids.append(process.pid)
            self.active_servers.append(len(self.server_pids))

    def pop(self):
        with self.lock:
            if len(self.server_pids) >= 1:
                pid = self.server_pids.pop()
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    self.active_servers.append(len(self.server_pids))
                except Exception:
                    pass  # El proceso ya no existe

    def pop_all(self):
        with self.lock:
            while len(self.server_pids) > 0:
                pid = self.server_pids.pop()
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                except Exception:
                    pass

    def count(self):
        with self.lock:
            return len(self.server_pids)

    def get_statistics(self):
        with self.lock:
            avg = math.ceil(sum(self.active_servers) / len(self.active_servers)) if self.active_servers else 0
            self.active_servers[:] = self.active_servers[-1:]
            return avg
