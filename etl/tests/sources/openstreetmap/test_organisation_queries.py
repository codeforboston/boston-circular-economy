"""Unit tests for the organization-specific OpenStreetMap filters.

Run offline and check the Overpass selectors built for each organization.
Live Overpass checks are in test_organization_queries_smoke.py.

    uv run pytest tests/sources/openstreetmap/test_organization_queries.py -v
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


def test_goodwill_filters_match_documented_example():
    # Keeps the example comment above ORGANIZATION_FILTERS in queries.py accurate.
    assert BY_KEY["goodwill"].filters() == [
        '["name"~"Goodwill",i]["shop"]',
        '["brand"~"Goodwill",i]["shop"]',
        '["operator"~"Goodwill",i]["shop"]',
        '["brand:wikidata"="Q5583655"]["shop"]',
    ]
