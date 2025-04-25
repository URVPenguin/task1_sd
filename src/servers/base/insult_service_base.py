from abc import ABC, abstractmethod

class InsultServiceBase(ABC):
    def __init__(self):
        self.insults = []
        self.broadcaster_active = False

    @abstractmethod
    def add_insult(self, insult: str):
        """Add insult if not already present"""
        pass

    @abstractmethod
    def get_all_insults(self):
        """Return all stored insults"""
        pass

    @abstractmethod
    def unregister_subscriber(self, callback_url: str):
        pass

    @abstractmethod
    def register_subscriber(self, callback_url: str):
        pass

    @abstractmethod
    def start_broadcaster(self, interval: int = 5):
        """Start broadcasting random insults periodically"""
        pass

    @abstractmethod
    def stop_broadcaster(self):
        """Stop the insult broadcaster"""
        pass

    @abstractmethod
    def notify_subscribers(self, insult: str):
        pass