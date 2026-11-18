from abc import ABC, abstractmethod

from contracts.domain import NormalizedLocation, Service

from etl.dtos import RawLocation


class BaseNormalizer(ABC):
    """
    Subclass this to implement a normalizer for a data source.

    normalize() should transform a list of RawLocations into
    NormalizedLocations, mapping source-specific fields to the
    shared schema.
    """

    def __init__(self, services: list[Service]):
        # Services every location from this query offers, e.g. clothing repair.
        self.services = services

    @abstractmethod
    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        pass
