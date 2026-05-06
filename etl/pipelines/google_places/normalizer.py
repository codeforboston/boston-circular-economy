from __future__ import annotations

from dtos import Activity, ItemCategory, NormalizedLocation, RawLocation
from base.normalizer import BaseNormalizer

from pipelines.google_places.common import normalize_google_place


class GooglePlacesRepairNormalizer(BaseNormalizer):
    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        return [
            NormalizedLocation(**normalize_google_place(
                raw.payload,
                data_source=raw.data_source,
                data_source_id=raw.data_source_id,
                item_category=ItemCategory.SHOES,
                activity=Activity.REPAIR_PAID,
            ))
            for raw in raw_locations
        ]


class GooglePlacesDonationNormalizer(BaseNormalizer):
    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        return [
            NormalizedLocation(**normalize_google_place(
                raw.payload,
                data_source=raw.data_source,
                data_source_id=raw.data_source_id,
                item_category=ItemCategory.CLOTHING,
                activity=Activity.DONATION_DROP,
            ))
            for raw in raw_locations
        ]
