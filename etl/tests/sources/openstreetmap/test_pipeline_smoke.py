import pytest



# --------------------------------------------------------------------------
# Smoke test: hits the live Overpass API.
# --------------------------------------------------------------------------

@pytest.mark.network
def test_smoke_fetch_against_live_overpass(querier, fetch_or_skip):
    results = fetch_or_skip(querier)

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
