from abc import ABC, abstractmethod

from contracts.domain import DataSource, NormalizedLocation, ServiceClaim


class BaseDataStore(ABC):
    """Subclass this to implement a new storage backend."""

    @abstractmethod
    def write_source_snapshot(
        self,
        source: DataSource,
        normalized_locations: list[NormalizedLocation],
    ) -> None:
        """Create or update NormalizedLocations for one source. Never deletes."""
        pass

    @abstractmethod
    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        """Load the latest NormalizedLocation snapshot for one source."""
        pass

    @abstractmethod
    def write_service_claims(
        self,
        service_claims: list[ServiceClaim],
    ) -> None:
        """Create or update ServiceClaims across all sources. Never deletes."""
        pass

    @abstractmethod
    def read_service_claims(self) -> list[ServiceClaim]:
        """Load all ServiceClaims across all sources."""
        pass

    @abstractmethod
    def write_output_locations(
        self,
        output_locations: list[NormalizedLocation],
    ) -> None:
        """Persist merged locations after deduplication across sources."""
        pass

    @abstractmethod
    def read_output_locations(self) -> list[NormalizedLocation]:
        """Load the merged locations after deduplication across sources."""
        pass
