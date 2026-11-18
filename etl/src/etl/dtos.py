from datetime import datetime
from typing import Any, TypedDict

from contracts.domain import DataSource, NormalizedLocation
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

# QueryArgs holds the constructor kwargs for one querier + normalizer run.
class QueryArgs(TypedDict):
    querier: dict[str, Any]
    normalizer: dict[str, Any]

# MatchGroup is the boundary between MergeProcessor.match() and .prioritize().
# Keyed by DataSource; a source is only present if it has a NormalizedLocation
# for this business. Never empty.
MatchGroup = dict[DataSource, NormalizedLocation]
