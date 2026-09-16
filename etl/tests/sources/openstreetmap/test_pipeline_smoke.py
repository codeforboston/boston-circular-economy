import pytest


@pytest.mark.network
def test_fetch_against_live_overpass(querier):
    results = querier.fetch()

    # Wide bounds: OSM data changes, so this only catches a broken query or an empty response.
    assert 20 < len(results) < 400, f"unexpected count: {len(results)}"

    ids = [r.data_source_id for r in results]
    assert len(ids) == len(set(ids)), "duplicate data_source_id in results"
    assert all(i.split("/")[0] in {"node", "way", "relation"} for i in ids)

    for raw in results:
        payload = raw.payload
        has_coords = ("lat" in payload and "lon" in payload) or "center" in payload
        assert has_coords, f"no coordinates: {raw.data_source_id}"
