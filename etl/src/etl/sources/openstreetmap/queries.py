"""
    Category + Organization-specific OpenStreetMap query definitions.

"""
from dataclasses import dataclass

from contracts.domain import Activity, ItemCategory, Service

from etl.dtos import QueryArgs


# --------------------------------------------------------------------------
# Category filters
# --------------------------------------------------------------------------

# Buy secondhand clothing
CLOTHING_RESALE_FILTERS = [
    '["shop"="second_hand"]',
    '["shop"="clothes"]["second_hand"="yes"]',
]

# Repair / alter clothing
CLOTHING_REPAIR_FILTERS = [
    '["shop"="tailor"]',
    '["craft"="tailor"]',
    '["repair"="clothes"]',
]

# Charity shops sell donated goods and accept donations
CHARITY_SHOP_FILTERS = [
    '["shop"="charity"]',
    '["charity"="yes"]',
]

# Clothing drop-off bins and recycling points
CLOTHING_DROP_OFF_FILTERS = [
    '["amenity"="recycling"]["recycling:clothes"="yes"]',
]

# Every category filter, for tests and for building a single combined query.
CLOTHING_FILTERS = (
    CLOTHING_RESALE_FILTERS
    + CLOTHING_REPAIR_FILTERS
    + CHARITY_SHOP_FILTERS
    + CLOTHING_DROP_OFF_FILTERS
)


# --------------------------------------------------------------------------
# Organization filters
# --------------------------------------------------------------------------

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

# Every organization, for tests and for building a single combined query.
ORGANIZATIONS = THRIFT_CHAINS + HABITAT_RESTORE + DONATION_BIN_OPERATORS

# Each organization expands to one selector per identity field, plus one for
# its Wikidata ID. E.g. Goodwill:
#     ["name"~"Goodwill",i]["shop"]
#     ["brand"~"Goodwill",i]["shop"]
#     ["operator"~"Goodwill",i]["shop"]
#     ["brand:wikidata"="Q5583655"]["shop"]
# The querier wraps each one as `nwr<selector>(bbox);` and unions (ORs) all
# the filters in one query into a single Overpass request.
ORGANIZATION_FILTERS = organization_filters(ORGANIZATIONS)


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------

# Each entry is one querier + normalizer run in scrape_to_local, so one
# Overpass request. A place can match more than one query.
OPENSTREETMAP_QUERY_ARGS: list[QueryArgs] = [
    {
        "querier": {"tag_filters": CLOTHING_RESALE_FILTERS},
        "normalizer": {
            "services": [
                Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
    {
        "querier": {"tag_filters": CLOTHING_REPAIR_FILTERS},
        "normalizer": {
            "services": [
                Service(activity=Activity.REPAIR_PAID, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
    {
        "querier": {"tag_filters": CHARITY_SHOP_FILTERS},
        "normalizer": {
            "services": [
                Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
    {
        "querier": {"tag_filters": CLOTHING_DROP_OFF_FILTERS},
        "normalizer": {
            "services": [
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
    {
        "querier": {"tag_filters": organization_filters(THRIFT_CHAINS)},
        "normalizer": {
            "services": [
                Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
    {
        "querier": {"tag_filters": organization_filters(HABITAT_RESTORE)},
        "normalizer": {
            "services": [
                Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.FURNITURE),
                Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.TOOLS),
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.FURNITURE),
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.TOOLS),
            ],
        },
    },
    {
        "querier": {"tag_filters": organization_filters(DONATION_BIN_OPERATORS)},
        "normalizer": {
            "services": [
                Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
            ],
        },
    },
]
