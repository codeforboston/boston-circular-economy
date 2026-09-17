from datetime import datetime
from enum import Enum

from contracts.domain import Activity, Address, ItemCategory
from pydantic import BaseModel

"""
DTOs for the location pipeline.

The two pipeline boundaries are:
  - RawLocation: querier → normalizer
  - NormalizedLocation: normalizer → data store

Everything else in this file is a supporting type for NormalizedLocation.
"""


# The supported data sources for local service providers.
class DataSource(str, Enum):
    GOOGLE_PLACES = "google_places"
    OPENSTREETMAP = "openstreetmap"


# RawLocation is the boundary between the querier and the normalizer.
class RawLocation(BaseModel):
    data_source: DataSource
    data_source_id: str
    fetched_at: datetime
    payload: dict


class Contact(BaseModel):
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    social: str | None = None


class Service(BaseModel):
    activity: Activity
    item_category: ItemCategory


class Availability(BaseModel):
    opening_hours: str | None = None
    is_persistent: bool = True


# NormalizedLocation is the boundary between the normalizer and the data store.
class NormalizedLocation(BaseModel):
    data_source_id: str  # unique identifier for this location within its data source
    data_source: DataSource
    name: str
    lat: float
    lon: float
    address: Address
    contact: Contact
    services: list[Service]
    availability: Availability
    last_verified: str | None = None


# MatchGroup is the boundary between MergeProcessor.match() and .prioritize().
# Keyed by DataSource; a source is only present if it has a NormalizedLocation
# for this business. Never empty.
MatchGroup = dict[DataSource, NormalizedLocation]
