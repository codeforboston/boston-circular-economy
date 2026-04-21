from abc import ABC, abstractmethod

from dtos import RawLocation


class BaseQuerier(ABC):
    """
    Subclass this to implement a new data source.

    fetch() should return all locations for the source,
    handling pagination internally if the API requires it.
    """

    @abstractmethod
    def fetch(self) -> list[RawLocation]:
        pass
