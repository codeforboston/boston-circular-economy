"""Tests for the OpenStreetMap querier.

Unit tests run offline and cover query building and RawLocation mapping.
The smoke test is marked `network` and hits the live Overpass API.

    uv run pytest tests/sources/openstreetmap/ -v            # everything
    uv run pytest tests/sources/openstreetmap/ -v -m "not network"   # offline only
    uv run pytest tests/sources/openstreetmap/ -v -m network -s     # smoke only, with output
"""

import pytest

from etl.dtos import DataSource, RawLocation
from etl.sources.openstreetmap.querier import DEFAULT_BBOX, OpenStreetMapQuerier

CLOTHING_FILTERS = [
    '["shop"="tailor"]',
    '["craft"="tailor"]',
    '["shop"="second_hand"]',
    '["shop"="clothes"]["second_hand"="yes"]',
    '["shop"="charity"]',
    '["amenity"="recycling"]["recycling:clothes"="yes"]',
]


# --------------------------------------------------------------------------
# Fixtures: hand-written Overpass elements.
# --------------------------------------------------------------------------

NODE_WITH_NAME = {
    "type": "node",
    "id": 2707308543,
    "lat": 42.3641243,
    "lon": -71.1019370,
    "tags": {"name": "Boomerangs", "shop": "second_hand"},
}

# Ways carry coordinates under "center", which only appears when the query
# ends with `out center;`.
WAY_WITH_CENTER = {
    "type": "way",
    "id": 674356526,
    "center": {"lat": 42.4626283, "lon": -70.9473823},
    "nodes": [6315476620, 6315476621],
    "tags": {"name": "The Salvation Army", "shop": "charity"},
}

# A real pattern from the donation data: a recycling container with no name.
UNNAMED_BIN = {
    "type": "node",
    "id": 13048760434,
    "lat": 42.3672692,
    "lon": -71.1148759,
    "tags": {
        "amenity": "recycling",
        "operator": "City of Cambridge",
        "recycling:clothes": "yes",
    },
}


@pytest.fixture
def querier():
    return OpenStreetMapQuerier(tag_filters=CLOTHING_FILTERS)


# --------------------------------------------------------------------------
# Unit tests: _build_query
# --------------------------------------------------------------------------

def test_build_query_exact_output():
    q = OpenStreetMapQuerier(tag_filters=['["shop"="tailor"]'], bbox=(1.0, 2.0, 3.0, 4.0), timeout_s=25)
    assert q._build_query() == '[out:json][timeout:25];(nwr["shop"="tailor"](1.0,2.0,3.0,4.0););out center;'


def test_build_query_unions_all_filters(querier):
    query = querier._build_query()
    for tag_filter in CLOTHING_FILTERS:
        assert tag_filter in query
    # one nwr statement per filter
    assert query.count("nwr") == len(CLOTHING_FILTERS)


def test_build_query_requests_center(querier):
    # Without `out center;` ways and relations come back with no coordinates.
    assert querier._build_query().endswith("out center;")


def test_build_query_uses_bbox_in_south_west_north_east_order(querier):
    south, west, north, east = DEFAULT_BBOX
    assert f"({south},{west},{north},{east})" in querier._build_query()


# --------------------------------------------------------------------------
# Unit tests: _to_raw_locations
# --------------------------------------------------------------------------

def test_to_raw_locations_builds_valid_dtos(querier):
    result = querier._to_raw_locations([NODE_WITH_NAME])
    assert len(result) == 1
    raw = result[0]
    assert isinstance(raw, RawLocation)
    assert raw.data_source is DataSource.OPENSTREETMAP
    assert raw.data_source_id == "node/2707308543"
    assert raw.fetched_at is not None


def test_data_source_id_includes_element_type(querier):
    # node/123 and way/123 are different objects; the type prefix keeps them distinct.
    same_id_different_types = [
        {"type": "node", "id": 123, "lat": 1.0, "lon": 2.0, "tags": {}},
        {"type": "way", "id": 123, "center": {"lat": 1.0, "lon": 2.0}, "tags": {}},
    ]
    result = querier._to_raw_locations(same_id_different_types)
    assert {r.data_source_id for r in result} == {"node/123", "way/123"}


def test_duplicate_elements_are_deduped(querier):
    # MergeProcessor.match() assumes no duplicate entries per source.
    result = querier._to_raw_locations([NODE_WITH_NAME, NODE_WITH_NAME, NODE_WITH_NAME])
    assert len(result) == 1


def test_payload_is_preserved_unmodified(querier):
    result = querier._to_raw_locations([WAY_WITH_CENTER])
    # Interpretation belongs to the normalizer, so the raw element passes through intact.
    assert result[0].payload == WAY_WITH_CENTER
    assert result[0].payload["center"] == {"lat": 42.4626283, "lon": -70.9473823}


def test_unnamed_elements_are_kept(querier):
    # Nameless donation bins are real data; dropping them is the normalizer's decision, not the querier's.
    result = querier._to_raw_locations([UNNAMED_BIN])
    assert len(result) == 1
    assert "name" not in result[0].payload["tags"]
    assert result[0].payload["tags"]["operator"] == "City of Cambridge"


def test_empty_response_returns_empty_list(querier):
    assert querier._to_raw_locations([]) == []


# --------------------------------------------------------------------------
# Smoke test: hits the live Overpass API.
# --------------------------------------------------------------------------

@pytest.mark.network
def test_smoke_fetch_against_live_overpass(querier):
    results = querier.fetch()

    print(f"\n  fetched {len(results)} locations")

    # Ballpark from prior Overpass Turbo runs (tailor ~23, second_hand ~18,
    # charity ~10, plus clothing recycling bins). Wide bounds — OSM data changes.
    assert 20 < len(results) < 400, f"unexpected count: {len(results)}"

    ids = [r.data_source_id for r in results]
    assert len(ids) == len(set(ids)), "duplicate data_source_id in results"
    assert all(i.split("/")[0] in {"node", "way", "relation"} for i in ids)

    # Every element must be placeable: nodes carry lat/lon, ways/relations carry center.
    for raw in results:
        p = raw.payload
        assert ("lat" in p and "lon" in p) or "center" in p, f"no coordinates: {raw.data_source_id}"

    named = [r for r in results if r.payload.get("tags", {}).get("name")]
    print(f"  {len(named)} named, {len(results) - len(named)} unnamed")

    shops = {}
    for raw in results:
        tags = raw.payload.get("tags", {})
        key = tags.get("shop") or tags.get("craft") or tags.get("amenity") or "(other)"
        shops[key] = shops.get(key, 0) + 1
    print(f"  breakdown: {dict(sorted(shops.items(), key=lambda kv: -kv[1]))}")
    print(f"  sample: {results[0].data_source_id} -> {results[0].payload.get('tags', {}).get('name')}")