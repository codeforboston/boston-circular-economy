from datetime import datetime, timezone

from base.querier import BaseQuerier
from dtos import RawLocation


MOCK_DATA = [
    {
        "id": "example-001",
        "name": "Beacon Hill Repair Cafe",
        "lat": 42.3588,
        "lon": -71.0707,
        "address": {
            "street": "74 Joy St",
            "city": "Boston",
            "state": "MA",
            "postcode": "02114",
        },
        "phone": "617-555-0101",
        "website": "https://example.com/beacon-hill-repair",
        "opening_hours": "Sa 10:00-14:00",
        "services": [
            {
                "activity": "repair_free",
                "item_category": "electronics",
            },
            {
                "activity": "repair_free",
                "item_category": "clothing",
            },
        ],
    },
    {
        "id": "example-002",
        "name": "Jamaica Plain Tool Library",
        "lat": 42.3100,
        "lon": -71.1132,
        "address": {
            "street": "301 Centre St",
            "city": "Boston",
            "state": "MA",
            "postcode": "02130",
        },
        "phone": "617-555-0102",
        "website": "https://example.com/jp-tool-library",
        "opening_hours": "We 17:00-20:00; Sa 10:00-13:00",
        "services": [
            {
                "activity": "borrowing",
                "item_category": "furniture",
            },
        ],
    },
]


class ExampleQuerier(BaseQuerier):

    def fetch(self) -> list[RawLocation]:
        fetched_at = datetime.now(timezone.utc)
        raw_locations = []
        for item in MOCK_DATA:
            raw_locations.append(RawLocation(
                data_source="example",
                data_source_id=item["id"],
                fetched_at=fetched_at,
                payload=item,
            ))
        return raw_locations
