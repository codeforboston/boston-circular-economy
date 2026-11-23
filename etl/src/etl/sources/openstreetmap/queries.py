"""
    All OpenStreetMap queries run by scrape_to_local.

    - item_queries/: find places by what they are (tags), one file per item category
    - org_queries.py: find places by who runs them

    Each entry is one query, so one Overpass request.
    A place can match more than one query.
"""
from etl.dtos import QueryArgs

from etl.sources.openstreetmap.item_queries import ITEM_QUERY_ARGS
from etl.sources.openstreetmap.org_queries import ORG_QUERY_ARGS


OPENSTREETMAP_QUERY_ARGS: list[QueryArgs] = ITEM_QUERY_ARGS + ORG_QUERY_ARGS
