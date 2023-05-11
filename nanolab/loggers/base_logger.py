from abc import ABC, abstractmethod


class AbstractLogger(ABC):

    @abstractmethod
    async def fetch_logs(self):
        pass