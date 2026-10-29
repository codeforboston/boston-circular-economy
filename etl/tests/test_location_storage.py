import json

import pytest
from contracts.domain import Contact, DataSource, Location, NormalizedLocation
from data_store import LocalDataStore

from etl.field_merge import merge_group
from etl.jobs.merge_process_to_local import main


@pytest.mark.parametrize("source", list(DataSource))
def test_snapshot_and_output_round_trip(tmp_path, make_location, source):
    store = LocalDataStore(tmp_path)
    normalized = make_location(data_source=source, data_source_id="same-id")
    store.write_source_snapshot(source, [normalized])
    snapshot = store.read_source_snapshot(source)
    assert snapshot == [normalized]
    assert type(snapshot[0]) is NormalizedLocation

    location = merge_group({source: snapshot[0]})
    store.write_output_locations([location])
    output = store.read_output_locations()
    assert output == [location]
    assert type(output[0]) is Location
    payload = json.loads((tmp_path / "output/locations.json").read_text())
    assert payload["locations"][0]["id"] == f"{source.value}:same-id"
    assert "data_source" not in payload["locations"][0]
    assert "data_source_id" not in payload["locations"][0]


def test_merge_job_writes_final_locations(tmp_path, make_location, monkeypatch):
    store = LocalDataStore(tmp_path)
    for source in DataSource:
        store.write_source_snapshot(source, [make_location(
            data_source=source, data_source_id="same-id", name="Same Business",
            lat=42.35, lon=-71.05, contact=Contact(phone="617-555-0100"),
        )])
    monkeypatch.setenv("ETL_DATA_DIR", str(tmp_path))
    main()
    output = store.read_output_locations()
    assert len(output) == 1
    assert type(output[0]) is Location
    assert output[0].id == "google_places:same-id"


def test_output_ids_distinguish_sources(tmp_path, make_location):
    store = LocalDataStore(tmp_path)
    locations = [merge_group({source: make_location(
        data_source=source, data_source_id="same-id",
    )}) for source in DataSource]
    store.write_output_locations(locations)
    assert len({loc.id for loc in store.read_output_locations()}) == 2
