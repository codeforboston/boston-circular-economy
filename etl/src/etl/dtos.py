from datetime import datetime
from typing import Any, TypedDict

from contracts.domain import DataSource, NormalizedLocation, Service
from pydantic import BaseModel

"""
DTOs for the location pipeline.

The three pipeline boundaries are:
  - RawLocation: querier → normalizer
  - NormalizedLocation: normalizer → data store (snapshot)
  - Location: merge_processor → data store (location)

Everything else in this file is a supporting type for NormalizedLocation.

Data objects migrated to contracts.domain, which is a dependency by other parts of the project.
"""

# RawLocation is the boundary between the querier and the normalizer.
class RawLocation(BaseModel):
    data_source: DataSource
    data_source_id: str
    fetched_at: datetime
    payload: dict

# NormalizerArgs are the constructor kwargs shared by every normalizer.
class NormalizerArgs(TypedDict):
    # Services every location returned by this query offers.
    services: list[Service]

# QueryArgs holds the constructor kwargs for one querier + normalizer run.
# Querier kwargs differ per source, so they stay a plain dict.
class QueryArgs(TypedDict):
    querier: dict[str, Any]
    normalizer: NormalizerArgs

# MatchGroup is the boundary between MergeProcessor.match() and .prioritize().
# Keyed by DataSource; a source is only present if it has a NormalizedLocation
# for this business. Never empty.
MatchGroup = dict[DataSource, NormalizedLocation]
