import pytest

from etl.dtos import (
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

    Each call returns a fresh instance, so tests needing multiple distinct
    locations can call this repeatedly without them sharing state.
    """

    def _make(**overrides) -> NormalizedLocation:
        defaults = dict(
            data_source_id="example-001",
            data_source=DataSource.GOOGLE_PLACES,
            name="Beacon Hill Repair Cafe",
            lat=42.3588,
            lon=-71.0707,
            address=Address(
                street="74 Joy St", city="Boston", state="MA", postcode="02114"
            ),
            contact=Contact(phone="617-555-0101", website="https://example.com"),
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
