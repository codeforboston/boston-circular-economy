import pytest

from etl.sources.openstreetmap.querier import OpenStreetMapQuerier


@pytest.fixture
def clothing_filters():
    return [
        '["shop"="tailor"]',
        '["craft"="tailor"]',
        '["shop"="second_hand"]',
        '["shop"="clothes"]["second_hand"="yes"]',
        '["shop"="charity"]',
        '["amenity"="recycling"]["recycling:clothes"="yes"]',
    ]


@pytest.fixture
def querier(clothing_filters):
    return OpenStreetMapQuerier(tag_filters=clothing_filters)
