"""
    Clothing OpenStreetMap queries, found by what a place is (its tags).
"""
from contracts.domain import Activity, ItemCategory, Service

from etl.dtos import QueryArgs


CLOTHING_QUERY_ARGS: list[QueryArgs] = [
    # Buy secondhand clothing
    {
        "querier": {
            "tag_filters": [
                '["shop"="second_hand"]',
                '["shop"="clothes"]["second_hand"="yes"]',
            ],
        },
        "services": [
            Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
        ],
    },
    # Repair / alter clothing
    {
        "querier": {
            "tag_filters": [
                '["shop"="tailor"]',
                '["craft"="tailor"]',
                '["repair"="clothes"]',
            ],
        },
        "services": [
            Service(activity=Activity.REPAIR_PAID, item_category=ItemCategory.CLOTHING),
        ],
    },
    # Charity shops sell donated goods and accept donations
    {
        "querier": {
            "tag_filters": [
                '["shop"="charity"]',
                '["charity"="yes"]',
            ],
        },
        "services": [
            Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING),
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
        ],
    },
    # Clothing drop-off bins and recycling points
    {
        "querier": {
            "tag_filters": [
                '["amenity"="recycling"]["recycling:clothes"="yes"]',
            ],
        },
        "services": [
            Service(activity=Activity.DONATION_DROP, item_category=ItemCategory.CLOTHING),
        ],
    },
]
