import random
from abc import ABC, abstractmethod

class MiddlewareTester(ABC):
    def __init__(self):
        self.insults = []
        self.work_queue = []

    @abstractmethod
    def start_server(self, port):
        pass

    @abstractmethod
    def connect_client(self, port):
        pass

    def generate_test_text(self):
        """Generate text that may contain insults"""
        base_text = "This is some sample text that might contain "
        insults = ["stupid", "idiot", "moron", "dumb"]
        non_insults = ["apple", "banana", "computer", "phone"]
        if random.random() > 0.7:  # 30% chance of insult
            return base_text + random.choice(insults)
        return base_text + random.choice(non_insults)

    def filter_text(self, text):
        """Replace insults with CENSORED"""
        insults = ["stupid", "idiot", "moron", "dumb"]
        for insult in insults:
            text = text.replace(insult, "CENSORED")
        return text