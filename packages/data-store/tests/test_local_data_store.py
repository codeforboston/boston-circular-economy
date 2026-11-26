import json

import pytest
from contracts.domain import Activity, DataSource, ItemCategory, ServiceClaim
from data_store import LocalDataStore


@pytest.fixture
def store(tmp_path):
    return LocalDataStore(tmp_path)


def test_write_read_snapshot_round_trip(store, make_location):
    locations = [make_location(data_source_id="a"), make_location(data_source_id="b")]

    store.write_source_snapshot(DataSource.GOOGLE_PLACES, locations)
    result = store.read_source_snapshot(DataSource.GOOGLE_PLACES)

    assert result == locations


def test_read_missing_snapshot_raises_file_not_found(store):
    with pytest.raises(FileNotFoundError):
        store.read_source_snapshot(DataSource.GOOGLE_PLACES)


def test_snapshots_are_isolated_per_source(store, make_location):
    google_locations = [
        make_location(data_source_id="g1", data_source=DataSource.GOOGLE_PLACES)
    ]
    osm_locations = [
        make_location(data_source_id="o1", data_source=DataSource.OPENSTREETMAP)
    ]

    store.write_source_snapshot(DataSource.GOOGLE_PLACES, google_locations)
    store.write_source_snapshot(DataSource.OPENSTREETMAP, osm_locations)

    assert store.read_source_snapshot(DataSource.GOOGLE_PLACES) == google_locations
    assert store.read_source_snapshot(DataSource.OPENSTREETMAP) == osm_locations


def test_write_source_snapshot_keeps_existing_records(store, make_location):
    existing_location = make_location(data_source_id="existing")
    new_location = make_location(data_source_id="new")

    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [existing_location])
    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [new_location])

    assert store.read_source_snapshot(DataSource.GOOGLE_PLACES) == [
        existing_location,
        new_location,
    ]


def test_write_source_snapshot_updates_existing_record(store, make_location):
    original_location = make_location(data_source_id="a", name="Location A")
    other_location = make_location(data_source_id="b")
    updated_location = original_location.model_copy(
        update={"name": "Location A (Updated)"}
    )

    store.write_source_snapshot(
        DataSource.GOOGLE_PLACES, [original_location, other_location]
    )
    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [updated_location])

    assert store.read_source_snapshot(DataSource.GOOGLE_PLACES) == [
        updated_location,
        other_location,
    ]


def test_write_source_snapshot_empty_list_keeps_existing(store, make_location):
    existing_location = make_location(data_source_id="existing")

    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [existing_location])
    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [])

    assert store.read_source_snapshot(DataSource.GOOGLE_PLACES) == [existing_location]


def test_write_empty_snapshot_produces_empty_list_on_read(store):
    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [])

    assert store.read_source_snapshot(DataSource.GOOGLE_PLACES) == []


def test_write_output_locations_writes_to_output_file(store, make_location, tmp_path):
    locations = [make_location(data_source_id="a"), make_location(data_source_id="b")]

    store.write_output_locations(locations)

    output_file = tmp_path / "output" / "locations.json"
    assert output_file.exists()
    with open(output_file) as file:
        payload = json.load(file)
    assert [item["data_source_id"] for item in payload["locations"]] == ["a", "b"]
    assert store.read_output_locations() == locations


def test_read_missing_output_locations_raises_file_not_found(store):
    with pytest.raises(FileNotFoundError):
        store.read_output_locations()


def test_write_creates_missing_data_dir(tmp_path, make_location):
    data_dir = tmp_path / "does-not-exist-yet"
    store = LocalDataStore(data_dir)

    store.write_source_snapshot(DataSource.GOOGLE_PLACES, [make_location()])

    assert data_dir.exists()


def make_claim(
    data_source_id="a",
    data_source=DataSource.GOOGLE_PLACES,
    activity=Activity.REPAIR_PAID,
    item_category=ItemCategory.CLOTHING,
):
    return ServiceClaim(
        data_source=data_source,
        data_source_id=data_source_id,
        activity=activity,
        item_category=item_category,
    )


def test_write_read_service_claims_round_trip(store):
    claims = [make_claim(data_source_id="a"), make_claim(data_source_id="b")]

    store.write_service_claims(claims)

    assert store.read_service_claims() == claims


def test_read_missing_service_claims_raises_file_not_found(store):
    with pytest.raises(FileNotFoundError):
        store.read_service_claims()


def test_write_service_claims_keeps_existing_claims(store):
    existing_claim = make_claim(data_source_id="existing")
    new_claim = make_claim(data_source_id="new")

    store.write_service_claims([existing_claim])
    store.write_service_claims([new_claim])

    assert store.read_service_claims() == [existing_claim, new_claim]


def test_write_service_claims_skips_duplicate_claims(store):
    claim = make_claim()

    store.write_service_claims([claim])
    store.write_service_claims([claim])

    assert store.read_service_claims() == [claim]


def test_one_location_can_have_many_service_claims(store):
    # The same location found by two queries gets one claim per service.
    repair_claim = make_claim(activity=Activity.REPAIR_PAID)
    resale_claim = make_claim(activity=Activity.RESALE_BUY)

    store.write_service_claims([repair_claim, resale_claim])

    assert store.read_service_claims() == [repair_claim, resale_claim]


def test_service_claims_from_different_sources_are_kept_apart(store):
    google_claim = make_claim(data_source=DataSource.GOOGLE_PLACES)
    osm_claim = make_claim(data_source=DataSource.OPENSTREETMAP)

    store.write_service_claims([google_claim, osm_claim])

    assert store.read_service_claims() == [google_claim, osm_claim]


def test_write_empty_service_claims_produces_empty_list_on_read(store):
    store.write_service_claims([])

    assert store.read_service_claims() == []
