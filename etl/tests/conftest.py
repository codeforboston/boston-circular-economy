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
