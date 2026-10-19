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


# --------------------------------------------------------------------------
# Per-organization tests: every organization is checked the same way.
# --------------------------------------------------------------------------

# Exact selectors for each organization, so its pattern, scope, fields and
# Wikidata ID are all pinned. Changing an organization's query should mean
# updating its row here. The goodwill row also keeps the example comment above
# ORGANIZATION_FILTERS in queries.py accurate.
EXPECTED_FILTERS = {
    "goodwill": [
        '["name"~"Goodwill",i]["shop"]',
        '["brand"~"Goodwill",i]["shop"]',
        '["operator"~"Goodwill",i]["shop"]',
        '["brand:wikidata"="Q5583655"]["shop"]',
    ],
    "salvation_army": [
        '["name"~"Salvation Army",i]["shop"]',
        '["brand"~"Salvation Army",i]["shop"]',
        '["operator"~"Salvation Army",i]["shop"]',
        '["brand:wikidata"="Q188307"]["shop"]',
    ],
    "savers": [
        '["name"~"^Savers$",i]["shop"]',
        '["brand"~"^Savers$",i]["shop"]',
        '["operator"~"^Savers$",i]["shop"]',
        '["brand:wikidata"="Q7428188"]["shop"]',
    ],
    "habitat_restore": [
        '["name"~"Habitat for Humanity",i]["shop"]',
        '["brand"~"Habitat for Humanity",i]["shop"]',
        '["operator"~"Habitat for Humanity",i]["shop"]',
        '["brand:wikidata"="Q108414596"]["shop"]',
    ],
    "planet_aid": [
        '["name"~"Planet Aid",i]["amenity"="recycling"]',
        '["brand"~"Planet Aid",i]["amenity"="recycling"]',
        '["operator"~"Planet Aid",i]["amenity"="recycling"]',
        '["brand:wikidata"="Q7201055"]["amenity"="recycling"]',
    ],
    # Donation bins only; the office and blood donation sites are out of scope.
    "red_cross": [
        '["name"~"Red Cross",i]["amenity"="recycling"]',
        '["brand"~"Red Cross",i]["amenity"="recycling"]',
        '["operator"~"Red Cross",i]["amenity"="recycling"]',
        '["brand:wikidata"="Q470110"]["amenity"="recycling"]',
    ],
    # Operator only, recycling sites only.
    "city_of_cambridge": [
        '["operator"~"City of Cambridge",i]["amenity"="recycling"]',
    ],
}

# Real-world tag values each pattern must accept (True) or reject (False).
# Every organization has at least one accepted value; rejected values are
# known false positives.
PATTERN_CASES = [
    ("goodwill", "Goodwill", True),
    ("goodwill", "Morgan Memorial Goodwill Industries", True),
    ("salvation_army", "The Salvation Army Family Store", True),
    ("savers", "Savers", True),
    ("savers", "Lifesavers Pharmacy", False),
    ("habitat_restore", "Habitat for Humanity ReStore", True),
    ("habitat_restore", "Restore Hyper Wellness", False),
    ("habitat_restore", "Restorers without Borders", False),
    ("planet_aid", "Planet Aid", True),
    ("red_cross", "American Red Cross", True),
    ("city_of_cambridge", "City of Cambridge", True),
]


def test_every_organization_has_expected_filters():
    assert set(EXPECTED_FILTERS) == set(BY_KEY)


@pytest.mark.parametrize("key", EXPECTED_FILTERS)
def test_organization_filters(key):
    assert BY_KEY[key].filters() == EXPECTED_FILTERS[key]


def test_every_organization_has_a_pattern_case():
    assert {key for key, _, matches in PATTERN_CASES if matches} == set(BY_KEY)


@pytest.mark.parametrize(
    "key,text,should_match", PATTERN_CASES,
    ids=[f"{k}-{t}" for k, t, _ in PATTERN_CASES],
)
def test_organization_pattern(key, text, should_match):
    assert bool(re.search(BY_KEY[key].pattern, text, re.I)) is should_match


# --------------------------------------------------------------------------
# Combined filters
# --------------------------------------------------------------------------

def test_organization_filters_are_unique():
    assert len(ORGANIZATION_FILTERS) == len(set(ORGANIZATION_FILTERS))


def test_organization_filters_build_a_valid_query_with_clothing_filters():
    q = OpenStreetMapQuerier(tag_filters=CLOTHING_FILTERS + ORGANIZATION_FILTERS)
    query = q._build_query()
    assert query.count("nwr") == len(CLOTHING_FILTERS) + len(ORGANIZATION_FILTERS)
    assert '["operator"~"City of Cambridge",i]["amenity"="recycling"]' in query
