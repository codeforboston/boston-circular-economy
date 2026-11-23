"""
    OpenStreetMap queries that find places by who runs them (name, brand,
    operator or Wikidata ID).
"""
from dataclasses import dataclass

from contracts.domain import Activity, ItemCategory, Service

from etl.dtos import QueryArgs


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


# Each organization expands to one selector per identity field, plus one for
# its Wikidata ID. E.g. Goodwill:
#     ["name"~"Goodwill",i]["shop"]
#     ["brand"~"Goodwill",i]["shop"]
#     ["operator"~"Goodwill",i]["shop"]
#     ["brand:wikidata"="Q5583655"]["shop"]
# The querier wraps each one as `nwr<selector>(bbox);` and unions (ORs) all
# the filters in one query into a single Overpass request.
def organization_filters(organizations: list[Organization]) -> list[str]:
    return [f for org in organizations for f in org.filters()]


# Wikidata IDs and scopes checked against live Overpass results for DEFAULT_BBOX.

# Thrift chains that sell secondhand clothing and accept donations.
THRIFT_CHAINS = [
    # "Goodwill" also matches operator="Morgan Memorial Goodwill Industries",
    # the regional operator of Boston-area Goodwill stores.
    Organization("goodwill", "Goodwill", '["shop"]', wikidata="Q5583655"),
    Organization("salvation_army", "Salvation Army", '["shop"]', wikidata="Q188307"),
    # Exact name: at least one Savers is tagged shop=department_store.
    Organization("savers", "^Savers$", '["shop"]', wikidata="Q7428188"),
]

# Sells donated furniture, tools and building materials, not clothing.
HABITAT_RESTORE = [
    # Not "ReStore": that also matches "Restore Hyper Wellness" and "Restorers without Borders".
    Organization("habitat_restore", "Habitat for Humanity", '["shop"]', wikidata="Q108414596"),
]

# Operators of clothing donation bins.
DONATION_BIN_OPERATORS = [
    Organization("planet_aid", "Planet Aid", '["amenity"="recycling"]', wikidata="Q7201055"),
    # Donation bins only; the office and blood donation sites are out of scope.
    Organization("red_cross", "Red Cross", '["amenity"="recycling"]', wikidata="Q470110"),
    # Identified only as an operator; limited to recycling sites for now.
    Organization("city_of_cambridge", "City of Cambridge", '["amenity"="recycling"]', fields=("operator",)),
]


ORG_QUERY_ARGS: list[QueryArgs] = [
    {
        "querier": {"tag_filters": organization_filters(THRIFT_CHAINS)},
        "services": [
            Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
        ],
    },
    {
        "querier": {"tag_filters": organization_filters(HABITAT_RESTORE)},
        "services": [
            Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.FURNITURE),
            Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.TOOLS),
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.FURNITURE),
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.TOOLS),
        ],
    },
    {
        "querier": {"tag_filters": organization_filters(DONATION_BIN_OPERATORS)},
        "services": [
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
        ],
    },
]
