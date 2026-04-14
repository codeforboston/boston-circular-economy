from abc import ABC, abstractmethod

from data_transfer_objects import FetchResponse, SQLQuery


class BaseNormalizer(ABC):

    @abstractmethod
    def normalize(self, batch: FetchResponse) -> list[SQLQuery]:
        pass

