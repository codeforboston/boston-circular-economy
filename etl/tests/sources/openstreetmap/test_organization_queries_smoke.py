"""Smoke tests for the organization-specific OpenStreetMap filters.

Marked `network`: they hit the live Overpass API with one shared request.
Offline unit tests are in test_organization_queries.py.

    uv run pytest tests/sources/openstreetmap/test_organization_queries_smoke.py -v -m network -s
"""

import re

import pytest

from etl.sources.openstreetmap.querier import OpenStreetMapQuerier
from etl.sources.openstreetmap.queries import ORGANIZATION_FILTERS, ORGANIZATIONS, Organization


def _matches(org: Organization, tags: dict) -> bool:
    if org.wikidata and tags.get("brand:wikidata") == org.wikidata:
        return True
    return any(re.search(org.pattern, tags.get(field, ""), re.I) for field in org.fields)


@pytest.fixture(scope="module")
def org_results():
    # One Overpass call shared by every smoke test, to stay within rate limits.
    return OpenStreetMapQuerier(tag_filters=ORGANIZATION_FILTERS).fetch()


@pytest.mark.network
@pytest.mark.parametrize("org", ORGANIZATIONS, ids=lambda o: o.key)
def test_smoke_each_organization_is_found(org, org_results):
    hits = [r for r in org_results if _matches(org, r.payload.get("tags", {}))]
    by_field = {
        field: sum(bool(re.search(org.pattern, r.payload["tags"].get(field, ""), re.I)) for r in hits)
        for field in org.fields
    }
    print(f"\n  {org.key}: {len(hits)} hits, by field {by_field}")
    assert hits, f"no OSM elements found for {org.key}"


@pytest.mark.network
def test_smoke_scope_excludes_unrelated_places(org_results):
    # Known false positives from an unscoped name search in Boston.
    for raw in org_results:
        tags = raw.payload.get("tags", {})
        assert tags.get("amenity") != "place_of_worship", raw.data_source_id   # Salvation Army churches
        assert tags.get("healthcare") != "blood_donation", raw.data_source_id  # Red Cross blood drive
        assert tags.get("leisure") != "park", raw.data_source_id               # City of Cambridge parks


@pytest.mark.network
def test_smoke_every_result_matches_a_known_organization(org_results):
    unmatched = [
        r.data_source_id for r in org_results
        if not any(_matches(org, r.payload.get("tags", {})) for org in ORGANIZATIONS)
    ]
    assert not unmatched, unmatched
