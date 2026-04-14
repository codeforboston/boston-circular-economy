import time
from abc import ABC, abstractmethod

from data_transfer_objects import FetchResponse


class BaseQuerier(ABC):
    page_delay_seconds: float = 0

    def fetch(self):
        n = 0
        while True:
            response = self.fetch_one(n)
            yield response
            if not response.has_more:
                break
            n += 1
            time.sleep(self.page_delay_seconds)

    @abstractmethod
    def fetch_one(self, n: int) -> FetchResponse:
        pass
