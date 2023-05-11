from abc import ABC, abstractmethod


class AbstractStorage(ABC):

    @abstractmethod
    def store_logs(self, logs: dict):
        pass