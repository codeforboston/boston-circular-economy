from contracts.domain import DataSource, LocationProvenance
from etl.field_merge import merge_group
from etl.resolve_id import resolve_location_ids

GOOGLE = DataSource.GOOGLE_PLACES
OSM = DataSource.OPENSTREETMAP


def _merged(make_location, source_to_id):
    """Build one merged location and its provenance from source IDs."""
    group = {
        source: make_location(data_source=source, data_source_id=source_id)
        for source, source_id in source_to_id.items()
    }
    location, provenance = merge_group(group)
    return [location], [provenance]


def test_exact_source_match_reuses_previous_id(make_location):
    locations, provenance = _merged(make_location, {GOOGLE: "g1", OSM: "o1"})
    previous = [
        LocationProvenance(
            location_id="previous-id",
            source_to_id={OSM: "o1", GOOGLE: "g1"},
        )
    ]

    resolved, resolved_provenance = resolve_location_ids(
        locations, provenance, previous
    )

    assert resolved[0].id == "previous-id"
    assert resolved_provenance[0].location_id == "previous-id"


def test_changed_sources_keep_new_id(make_location):
    locations, provenance = _merged(make_location, {GOOGLE: "g1", OSM: "o1"})
    new_id = locations[0].id
    previous = [
        LocationProvenance(location_id="previous-id", source_to_id={GOOGLE: "g1"})
    ]

    resolved, resolved_provenance = resolve_location_ids(
        locations, provenance, previous
    )

    assert resolved[0].id == new_id
    assert resolved_provenance[0].location_id == new_id


def test_no_previous_provenance_keeps_new_id(make_location):
    locations, provenance = _merged(make_location, {GOOGLE: "g1"})
    new_id = locations[0].id

    resolved, resolved_provenance = resolve_location_ids(locations, provenance, [])

    assert resolved[0].id == new_id
    assert resolved_provenance[0].location_id == new_id
