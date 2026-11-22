"""
    OpenStreetMap queries that find places by what they are (their tags).
    One file per item category.
"""
from etl.dtos import QueryArgs

from etl.sources.openstreetmap.item_queries.clothing import CLOTHING_QUERY_ARGS


ITEM_QUERY_ARGS: list[QueryArgs] = CLOTHING_QUERY_ARGS
