from abc import ABC, abstractmethod

from dtos import RawLocation, NormalizedLocation


class BaseNormalizer(ABC):
    """
    Subclass this to implement a normalizer for a data source.

    normalize() should transform a list of RawLocations into
    NormalizedLocations, mapping source-specific fields to the
    shared schema.
    """

    @abstractmethod
    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        pass
