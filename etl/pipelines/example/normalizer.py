from base.normalizer import BaseNormalizer
from dtos import (
    RawLocation,
    NormalizedLocation,
    Address,
    Contact,
    Service,
    Activity,
    ItemCategory,
    Availability,
)


class ExampleNormalizer(BaseNormalizer):

    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        normalized_locations = []
        for raw in raw_locations:
            payload = raw.payload
            services = []
            for raw_service in payload["services"]:
                services.append(Service(
                    activity=Activity(raw_service["activity"]),
                    item_category=ItemCategory(raw_service["item_category"]),
                ))
            normalized_locations.append(NormalizedLocation(
                data_source_id=raw.data_source_id,
                data_source="example",
                name=payload["name"],
                lat=payload["lat"],
                lon=payload["lon"],
                address=Address(
                    street=payload["address"]["street"],
                    city=payload["address"]["city"],
                    state=payload["address"]["state"],
                    postcode=payload["address"]["postcode"],
                ),
                contact=Contact(
                    phone=payload.get("phone"),
                    website=payload.get("website"),
                ),
                services=services,
                availability=Availability(
                    opening_hours=payload.get("opening_hours"),
                ),
            ))
        return normalized_locations
