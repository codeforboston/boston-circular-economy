from datetime import datetime
from typing import Any, TypedDict

from contracts.domain import DataSource, NormalizedLocation, Service
from pydantic import BaseModel

"""
DTOs for the location pipeline.

The two pipeline boundaries are:
  - RawLocation: querier → normalizer
  - NormalizedLocation: normalizer → data store

Everything else in this file is a supporting type for NormalizedLocation.

Data objects migrated to contracts.domain, which is a dependency by other parts of the project.
"""

# RawLocation is the boundary between the querier and the normalizer.
class RawLocation(BaseModel):
    data_source: DataSource
    data_source_id: str
    fetched_at: datetime
    payload: dict

# QueryArgs describes one query: how to run the querier and what its results offer.
# Querier kwargs differ per source, so they stay a plain dict.
class QueryArgs(TypedDict):
    querier: dict[str, Any]
    # Services every location returned by this query offers.
    services: list[Service]

# MatchGroup is the boundary between MergeProcessor.match() and .prioritize().
# Keyed by DataSource; a source is only present if it has a NormalizedLocation
# for this business. Never empty.
MatchGroup = dict[DataSource, NormalizedLocation]
