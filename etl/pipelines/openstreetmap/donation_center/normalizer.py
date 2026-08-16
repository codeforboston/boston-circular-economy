from base.normalizer import BaseNormalizer
from dtos import (
    Activity,
    NormalizedLocation,
    RawLocation,
)
from pipelines.openstreetmap.donation_center.querier import DATA_SOURCE
from pipelines.openstreetmap.openstreetmap_common import (
    build_normalized_location
)


class DonationCenterNormalizer(BaseNormalizer):

    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        normalized_locations = []
        for raw in raw_locations:
            location = build_normalized_location(raw, DATA_SOURCE, self._get_activities)
            if location is not None:
                normalized_locations.append(location)
        return normalized_locations

    @staticmethod
    def _get_activities(tags: dict) -> list[Activity]:
        # Charity shops both accept donations and resell them.
        activities = [Activity.DONATION_DROP]
        if tags.get("shop") == "charity" or tags.get("second_hand") in ("yes", "only"):
            activities.append(Activity.RESALE_BUY)

        return activities
