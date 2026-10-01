"""Tests for the organization-specific OpenStreetMap filters.

Unit tests run offline and check the Overpass selectors built for each
organization. Smoke tests are marked `network` and hit the live Overpass API.

    uv run pytest tests/sources/openstreetmap/test_organization_queries.py -v
    uv run pytest tests/sources/openstreetmap/test_organization_queries.py -v -m network -s
"""

import re

import pytest

from etl.sources.openstreetmap.querier import OpenStreetMapQuerier
from etl.sources.openstreetmap.queries import (
    CLOTHING_FILTERS,
    ORGANIZATION_FILTERS,
    ORGANIZATIONS,
    Organization,
)

BY_KEY = {org.key: org for org in ORGANIZATIONS}


# --------------------------------------------------------------------------
# Unit tests: Organization.filters
# --------------------------------------------------------------------------

def test_filters_exact_output():
    org = Organization("acme", "Acme", '["shop"]', wikidata="Q1")
    assert org.filters() == [
        '["name"~"Acme",i]["shop"]',
        '["brand"~"Acme",i]["shop"]',
        '["operator"~"Acme",i]["shop"]',
        '["brand:wikidata"="Q1"]["shop"]',
    ]


def test_filters_without_wikidata_skip_wikidata_selector():
    org = Organization("acme", "Acme", '["shop"]')
    assert not any("wikidata" in f for f in org.filters())


@pytest.mark.parametrize("org", ORGANIZATIONS, ids=lambda o: o.key)
def test_each_field_gets_its_own_selector(org):
    # name, brand and operator are often out of sync in OSM, so each is queried separately.
    filters = org.filters()
    for field in org.fields:
        assert sum(f.startswith(f'["{field}"~') for f in filters) == 1


@pytest.mark.parametrize("org", ORGANIZATIONS, ids=lambda o: o.key)
def test_every_selector_carries_the_category_scope(org):
    # Without the scope, name matches pull in churches, parks, blood drives, etc.
    for f in org.filters():
        assert f.endswith(org.scope), f


def test_selectors_are_case_insensitive():
    for f in ORGANIZATION_FILTERS:
        if "~" in f:
            assert ",i]" in f, f


def test_red_cross_limited_to_donation_bins():
    assert BY_KEY["red_cross"].scope == '["amenity"="recycling"]'


def test_city_of_cambridge_is_operator_only_recycling():
    org = BY_KEY["city_of_cambridge"]
    assert org.filters() == ['["operator"~"City of Cambridge",i]["amenity"="recycling"]']


def test_goodwill_pattern_covers_morgan_memorial_operator():
    assert re.search(BY_KEY["goodwill"].pattern, "Morgan Memorial Goodwill Industries", re.I)


def test_habitat_pattern_rejects_unrelated_restore_names():
    pattern = BY_KEY["habitat_restore"].pattern
    assert re.search(pattern, "Habitat for Humanity ReStore", re.I)
    assert not re.search(pattern, "Restore Hyper Wellness", re.I)
    assert not re.search(pattern, "Restorers without Borders", re.I)


def test_savers_pattern_is_exact_name():
    pattern = BY_KEY["savers"].pattern
    assert re.search(pattern, "Savers", re.I)
    assert not re.search(pattern, "Lifesavers Pharmacy", re.I)


def test_organization_filters_are_unique():
    assert len(ORGANIZATION_FILTERS) == len(set(ORGANIZATION_FILTERS))


def test_organization_filters_build_a_valid_query_with_clothing_filters():
    q = OpenStreetMapQuerier(tag_filters=CLOTHING_FILTERS + ORGANIZATION_FILTERS)
    query = q._build_query()
    assert query.count("nwr") == len(CLOTHING_FILTERS) + len(ORGANIZATION_FILTERS)
    assert '["operator"~"City of Cambridge",i]["amenity"="recycling"]' in query


# --------------------------------------------------------------------------
# Smoke tests: hit the live Overpass API.
# --------------------------------------------------------------------------

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
