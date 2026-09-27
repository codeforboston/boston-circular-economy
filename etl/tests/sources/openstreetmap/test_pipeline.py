from etl.dtos import DataSource, RawLocation
from etl.sources.openstreetmap.querier import DEFAULT_BBOX, OpenStreetMapQuerier

NODE_WITH_NAME = {
    "type": "node",
    "id": 2707308543,
    "lat": 42.3641243,
    "lon": -71.1019370,
    "tags": {"name": "Boomerangs", "shop": "second_hand"},
}

# Ways carry coordinates under "center", which only appears when the query ends with `out center;`.
WAY_WITH_CENTER = {
    "type": "way",
    "id": 674356526,
    "center": {"lat": 42.4626283, "lon": -70.9473823},
    "nodes": [6315476620, 6315476621],
    "tags": {"name": "The Salvation Army", "shop": "charity"},
}

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


def test_build_query_exact_output():
    querier = OpenStreetMapQuerier(
        tag_filters=['["shop"="tailor"]'], bbox=(1.0, 2.0, 3.0, 4.0), timeout_s=25
    )

    assert querier._build_query() == (
        '[out:json][timeout:25];(nwr["shop"="tailor"](1.0,2.0,3.0,4.0););out center;'
    )


def test_build_query_unions_all_filters(querier, clothing_filters):
    query = querier._build_query()

    for tag_filter in clothing_filters:
        assert tag_filter in query
    assert query.count("nwr") == len(clothing_filters)


def test_build_query_requests_center(querier):
    # Without `out center;` ways and relations come back with no coordinates.
    assert querier._build_query().endswith("out center;")


def test_build_query_uses_bbox_in_south_west_north_east_order(querier):
    south, west, north, east = DEFAULT_BBOX

    assert f"({south},{west},{north},{east})" in querier._build_query()


def test_to_raw_locations_builds_valid_dtos(querier):
    result = querier._to_raw_locations([NODE_WITH_NAME])

    assert len(result) == 1
    assert isinstance(result[0], RawLocation)
    assert result[0].data_source is DataSource.OPENSTREETMAP
    assert result[0].data_source_id == "node/2707308543"
    assert result[0].fetched_at is not None


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
    # Interpretation belongs to the normalizer, so the raw element passes through intact.
    result = querier._to_raw_locations([WAY_WITH_CENTER])

    assert result[0].payload == WAY_WITH_CENTER


def test_unnamed_elements_are_kept(querier):
    # Dropping nameless donation bins is the normalizer's decision, not the querier's.
    result = querier._to_raw_locations([UNNAMED_BIN])

    assert len(result) == 1
    assert "name" not in result[0].payload["tags"]


def test_empty_response_returns_empty_list(querier):
    assert querier._to_raw_locations([]) == []
