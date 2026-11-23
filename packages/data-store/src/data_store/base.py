from abc import ABC, abstractmethod

from contracts.domain import (
    DataSource,
    Location,
    LocationProvenance,
    NormalizedLocation,
    ServiceClaim,
)


class BaseDataStore(ABC):
    """Subclass this to implement a new storage backend."""

    @abstractmethod
    def write_source_snapshot(
        self,
        source: DataSource,
        normalized_locations: list[NormalizedLocation],
    ) -> None:
        """Create or update NormalizedLocations for one source. Never deletes."""

    @abstractmethod
    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        """Load the latest NormalizedLocation snapshot for one source."""

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
        output_locations: list[Location],
    ) -> None:
        """Persist merged locations after deduplication across sources."""

    @abstractmethod
    def read_output_locations(self) -> list[Location]:
        """Load the merged locations after deduplication across sources."""

    @abstractmethod
    def write_location_provenance(
        self,
        location_provenance: list[LocationProvenance],
    ) -> None:
        """Persist location provenance information."""

    @abstractmethod
    def read_location_provenance(self) -> list[LocationProvenance]:
        """Load the location provenance information."""
