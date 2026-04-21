from abc import ABC, abstractmethod

from dtos import NormalizedLocation


class BaseIngester(ABC):
    """
    Subclass this to implement a new ingestion target.

    ingest() should persist a list of NormalizedLocations
    to the target (e.g. a database or file).
    """

    @abstractmethod
    def ingest(self, normalized_locations: list[NormalizedLocation]) -> None:
        pass
