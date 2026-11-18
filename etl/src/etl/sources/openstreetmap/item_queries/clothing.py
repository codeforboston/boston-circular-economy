"""
    Clothing OpenStreetMap queries, found by what a place is (its tags).
"""
from contracts.domain import Activity, ItemCategory, Service

from etl.dtos import QueryArgs


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


CLOTHING_QUERY_ARGS: list[QueryArgs] = [
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
]
