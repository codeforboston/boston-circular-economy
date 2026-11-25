from contracts.domain import (
    Address,
    Availability,
    Contact,
    DataSource,
    NormalizedLocation,
)

from etl.sources.openstreetmap.normalizer import OpenStreetMapNormalizer


def test_complete_node_is_normalized(make_raw_location):
    # Setup
    raw = make_raw_location(
        data_source_id="node/1",
        payload={
            "type": "node",
            "id": 1,
            "lat": 42.36,
            "lon": -71.06,
            "tags": {
                "name": "Re-Use Shop",
                "addr:housenumber": "12",
                "addr:street": "Main Street",
                "addr:city": "Boston",
                "addr:state": "MA",
                "addr:postcode": "02114",
                "phone": "+1 617 555 0100",
                "website": "https://example.com",
                "opening_hours": "Mo-Fr 09:00-17:00",
            },
        },
    )

    # Execute
    [loc] = OpenStreetMapNormalizer().normalize([raw])

    # Verify
    assert loc == NormalizedLocation(
        data_source_id="node/1",
        data_source=DataSource.OPENSTREETMAP,
        name="Re-Use Shop",
        lat=42.36,
        lon=-71.06,
        address=Address(
            street="12 Main Street", city="Boston", state="MA", postcode="02114"
        ),
        contact=Contact(phone="+1 617 555 0100", website="https://example.com"),
        services=[],
        availability=Availability(opening_hours="Mo-Fr 09:00-17:00"),
    )


def test_way_uses_center_coordinates(make_raw_location):
    # Setup
    raw = make_raw_location(
        payload={
            "type": "way",
            "id": 2,
            "center": {"lat": 42.37, "lon": -71.07},
            "tags": {"name": "Big Store"},
        },
    )

    # Execute
    [loc] = OpenStreetMapNormalizer().normalize([raw])

    # Verify
    assert loc == NormalizedLocation(
        data_source_id=raw.data_source_id,
        data_source=DataSource.OPENSTREETMAP,
        name="Big Store",
        lat=42.37,
        lon=-71.07,
        address=Address(),
        contact=Contact(),
        services=[],
        availability=Availability(),
    )


def test_contact_prefix_fallback(make_raw_location):
    # Setup
    both = make_raw_location(
        tags={
            "name": "Both",
            "phone": "+1 617 555 0100",
            "contact:phone": "+1 617 555 0101",
            "website": "https://example.com",
            "contact:website": "https://prefixed.example.com",
        }
    )
    blank_bare = make_raw_location(
        tags={
            "name": "Blank Bare",
            "phone": "  ",
            "contact:phone": "+1 617 555 0101",
            "contact:website": "https://prefixed.example.com",
        }
    )

    # Execute
    both_loc, blank_loc = OpenStreetMapNormalizer().normalize([both, blank_bare])

    # Verify
    assert both_loc.contact == Contact(
        phone="+1 617 555 0100", website="https://example.com"
    )
    assert blank_loc.contact == Contact(
        phone="+1 617 555 0101", website="https://prefixed.example.com"
    )


def test_street_without_housenumber(make_raw_location):
    # Setup
    raw = make_raw_location(tags={"name": "Street Only", "addr:street": "Main Street"})

    # Execute
    [loc] = OpenStreetMapNormalizer().normalize([raw])

    # Verify
    assert loc.address == Address(street="Main Street")


def test_missing_optional_fields_become_none(make_raw_location):
    # Setup
    raw = make_raw_location(tags={"name": "Name Only"})

    # Execute
    [loc] = OpenStreetMapNormalizer().normalize([raw])

    # Verify
    assert loc == NormalizedLocation(
        data_source_id=raw.data_source_id,
        data_source=DataSource.OPENSTREETMAP,
        name="Name Only",
        lat=raw.payload["lat"],
        lon=raw.payload["lon"],
        address=Address(),
        contact=Contact(),
        services=[],
        availability=Availability(),
    )


def test_missing_name_is_skipped(make_raw_location):
    # Setup
    no_name = make_raw_location(tags={})
    blank_name = make_raw_location(tags={"name": "  "})
    valid = make_raw_location(tags={"name": "Valid"})

    # Execute
    result = OpenStreetMapNormalizer().normalize([no_name, blank_name, valid])

    # Verify
    assert [loc.data_source_id for loc in result] == [valid.data_source_id]


def test_missing_coordinates_are_skipped(make_raw_location):
    # Setup
    way = make_raw_location(
        payload={"type": "way", "id": 3, "tags": {"name": "No Center"}},
    )
    node = make_raw_location(
        payload={"type": "node", "id": 4, "tags": {"name": "No Coordinates"}},
    )

    # Execute
    result = OpenStreetMapNormalizer().normalize([way, node])

    # Verify
    assert result == []
