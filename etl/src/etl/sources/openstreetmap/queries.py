"""
    Category + Organization-specific OpenStreetMap query definitions.
    
"""
from dataclasses import dataclass


CLOTHING_FILTERS = [
    # Resale (buy/sell secondhand clothing)
    '["shop"="second_hand"]',
    '["shop"="clothes"]["second_hand"="yes"]',
    # Repair / alter
    '["shop"="tailor"]',
    '["craft"="tailor"]',
    '["repair"="clothes"]',
    # Donation (drop-off)
    '["shop"="charity"]',
    '["charity"="yes"]',
    '["amenity"="recycling"]["recycling:clothes"="yes"]',
]


@dataclass(frozen=True)
class Organization:
    """Define how to find an organization in OpenStreetMap.

    Matches use the organization's identity tags and must also match `scope`
    to avoid unrelated places with similar names.
    """

    key: str
    # Overpass regex, matched case-insensitively against each of `fields`
    pattern: str
    scope: str
    wikidata: str | None = None
    fields: tuple[str, ...] = ("name", "brand", "operator")

    def filters(self) -> list[str]:
        selectors = [f'["{field}"~"{self.pattern}",i]{self.scope}' for field in self.fields]
        if self.wikidata:
            selectors.append(f'["brand:wikidata"="{self.wikidata}"]{self.scope}')
        return selectors



# Wikidata IDs and scopes checked against live Overpass results for DEFAULT_BBOX.
ORGANIZATIONS = [
    # "Goodwill" also matches operator="Morgan Memorial Goodwill Industries",
    # the regional operator of Boston-area Goodwill stores.
    Organization("goodwill", "Goodwill", '["shop"]', wikidata="Q5583655"),
    Organization("salvation_army", "Salvation Army", '["shop"]', wikidata="Q188307"),
    # Exact name: at least one Savers is tagged shop=department_store.
    Organization("savers", "^Savers$", '["shop"]', wikidata="Q7428188"),
    # Not "ReStore": that also matches "Restore Hyper Wellness" and "Restorers without Borders".
    Organization("habitat_restore", "Habitat for Humanity", '["shop"]', wikidata="Q108414596"),
    Organization("planet_aid", "Planet Aid", '["amenity"="recycling"]', wikidata="Q7201055"),
    # Donation bins only; the office and blood donation sites are out of scope.
    Organization("red_cross", "Red Cross", '["amenity"="recycling"]', wikidata="Q470110"),
    # Identified only as an operator; limited to recycling sites for now.
    Organization("city_of_cambridge", "City of Cambridge", '["amenity"="recycling"]', fields=("operator",)),
]

# Each organization expands to one selector per identity field, plus one for
# its Wikidata ID. E.g. Goodwill:
#     ["name"~"Goodwill",i]["shop"]
#     ["brand"~"Goodwill",i]["shop"]
#     ["operator"~"Goodwill",i]["shop"]
#     ["brand:wikidata"="Q5583655"]["shop"]
# The querier wraps each one as `nwr<selector>(bbox);` and unions (ORs) them
# all, together with CLOTHING_FILTERS, into a single Overpass request.
ORGANIZATION_FILTERS = [f for org in ORGANIZATIONS for f in org.filters()]
