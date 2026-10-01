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


# Organization identifiers and scopes verified against live Overpass results.
ORGANIZATIONS = [
    # Includes the regional operator of Boston-area Goodwill stores.
    Organization("goodwill", "Goodwill", '["shop"]', wikidata="Q5583655"),
    Organization("salvation_army", "Salvation Army", '["shop"]', wikidata="Q188307"),
    # Exact name; some locations use shop=department_store.
    Organization("savers", "^Savers$", '["shop"]', wikidata="Q7428188"),
    # Match Habitat for Humanity locations without matching unrelated "Restore" names.
    Organization("habitat_restore", "Habitat for Humanity", '["shop"]', wikidata="Q108414596"),
    Organization("planet_aid", "Planet Aid", '["amenity"="recycling"]', wikidata="Q7201055"),
    # Limit matches to donation bins, excluding offices and blood donation sites.
    Organization("red_cross", "Red Cross", '["amenity"="recycling"]', wikidata="Q470110"),
    # Identified by operator and limited to recycling sites.
    Organization("city_of_cambridge", "City of Cambridge", '["amenity"="recycling"]', fields=("operator",)),
]

ORGANIZATION_FILTERS = [f for org in ORGANIZATIONS for f in org.filters()]
