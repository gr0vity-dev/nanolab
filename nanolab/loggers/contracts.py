from abc import ABC, abstractmethod
from dataclasses import dataclass


class ILogger(ABC):

    @abstractmethod
    async def fetch_logs(self):
        pass


class ISink(ABC):

    @abstractmethod
    def store_logs(self, logs: dict):
        pass


@dataclass
class LogData:
    node_name: str
    node_version: str
    elapsed_time: int
    check_count: int
    cemented_count: int
    cps: int
    bps: int
    timestamp: str
    percent_cemented: float
    percent_checked: float