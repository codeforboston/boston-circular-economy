"""
    Google Places query definitions.
"""
from etl.dtos import QueryArgs


# Each entry is one querier + normalizer run in scrape_to_local.
GOOGLE_PLACES_QUERY_ARGS: list[QueryArgs] = []
