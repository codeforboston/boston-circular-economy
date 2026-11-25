from datetime import datetime, timezone

import pytest
from contracts.domain import (
    Activity,
    Address,
    Availability,
    Contact,
    DataSource,
    ItemCategory,
    NormalizedLocation,
    Service,
)

from etl.dtos import RawLocation


@pytest.fixture
def make_location():
    """Factory for a valid NormalizedLocation, with overridable fields.

    Each call generates unique values for matching-critical fields (name, lat, lon, phone)
    to prevent accidental matches in tests. Tests that want locations to match should
    explicitly provide matching values.
    """
    counter = {"count": 0}

    def _make(**overrides) -> NormalizedLocation:
        counter["count"] += 1
        n = counter["count"]

        # Generate unique defaults for matching-critical fields
        # Spread locations across Boston area to avoid distance-based matches
        defaults = dict(
            data_source_id=f"test-{n:03d}",
            data_source=DataSource.GOOGLE_PLACES,
            name=f"Test Business {n}",
            lat=42.35 + (n * 0.01),  # Spread north-south
            lon=-71.05 - (n * 0.01),  # Spread east-west
            address=Address(
                street=f"{n} Test St", city="Boston", state="MA", postcode="02114"
            ),
            contact=Contact(phone=f"617-555-{n:04d}", website="https://example.com"),
            services=[
                Service(
                    activity=Activity.REPAIR_FREE,
                    item_category=ItemCategory.ELECTRONICS,
                )
            ],
            availability=Availability(opening_hours="Sa 10:00-14:00"),
        )
        defaults.update(overrides)
        return NormalizedLocation(**defaults)

    return _make


@pytest.fixture
def make_raw_location():
    """Factory for an OpenStreetMap RawLocation, with overridable fields.

    `tags` replaces the default node's tags (no merge); `payload` replaces the
    whole payload. The default data_source_id is built from the payload as
    "{type}/{id}", the same way the querier builds it.
    """
    counter = {"count": 0}

    def _make(tags: dict | None = None, **overrides) -> RawLocation:
        counter["count"] += 1
        n = counter["count"]

        payload = overrides.pop("payload", None) or {
            "type": "node",
            "id": n,
            "lat": 42.35 + (n * 0.01),
            "lon": -71.05 - (n * 0.01),
            "tags": tags if tags is not None else {"name": f"Test Business {n}"},
        }

        defaults = dict(
            data_source=DataSource.OPENSTREETMAP,
            data_source_id=f"{payload['type']}/{payload['id']}",
            fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            payload=payload,
        )
        defaults.update(overrides)
        return RawLocation(**defaults)

    return _make
