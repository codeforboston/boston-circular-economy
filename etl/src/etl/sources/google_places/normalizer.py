from contracts.domain import NormalizedLocation

from etl.base.normalizer import BaseNormalizer
from etl.dtos import RawLocation


class GooglePlacesNormalizer(BaseNormalizer):

    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        pass
