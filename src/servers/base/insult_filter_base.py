from abc import ABC, abstractmethod
from collections import deque


class InsultFilterBase(ABC):
    def __init__(self):
        self.results = deque(maxlen=100)
        self.insults = {"stupid", "idiot", "dumb", "moron", "jerk"}

    @abstractmethod
    def process_queue(self):
        pass

    @abstractmethod
    def submit_text(self, text):
        """Add text to be filtered"""
        pass

    @abstractmethod
    def get_results(self):
        """Get all filtered results"""
        pass

    def filter_text(self, text):
        for insult in self.insults:
            text = text.replace(insult, "CENSORED")
        return text