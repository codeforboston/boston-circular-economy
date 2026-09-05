from abc import ABC, abstractmethod

from etl.dtos import DataSource, NormalizedLocation


class BaseDataStore(ABC):
    """
    Subclass this to implement a new storage backend.
    """

    @abstractmethod
    def write_source_snapshot(
        self,
        source: DataSource,
        normalized_locations: list[NormalizedLocation],
    ) -> None:
        """Persist a full snapshot of NormalizedLocations for one source."""
        pass

    @abstractmethod
    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        """Load the latest NormalizedLocation snapshot for one source."""
        pass

    @abstractmethod
    def write_output_locations(
        self,
        output_locations: list[NormalizedLocation],
    ) -> None:
        """Persist locations after they have been deduplicated across sources."""
        pass
