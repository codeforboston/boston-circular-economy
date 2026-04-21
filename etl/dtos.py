from datetime import datetime
from enum import Enum

from pydantic import BaseModel

# DTOs for the location pipeline.
#
# The two pipeline boundaries are:
#   - RawLocation: querier → normalizer
#   - NormalizedLocation: normalizer → ingester
#
# Everything else in this file is a supporting type for NormalizedLocation.


# RawLocation is the boundary between the querier and the normalizer.
class RawLocation(BaseModel):
    data_source: str
    data_source_id: str
    fetched_at: datetime
    payload: dict


class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None


class Contact(BaseModel):
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    social: str | None = None


class Activity(str, Enum):
    REPAIR = "repair"
    DONATION = "donation"
    RESALE = "resale"
    REFILL = "refill"
    LENDING = "lending"


class ItemCategory(str, Enum):
    SHOES = "shoes"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    FURNITURE = "furniture"


class Direction(str, Enum):
    SOURCE = "source"
    DESTINATION = "destination"


class Service(BaseModel):
    activity: Activity
    item_category: ItemCategory
    direction: Direction


class Availability(BaseModel):
    opening_hours: str | None = None
    is_persistent: bool = True


# NormalizedLocation is the boundary between the normalizer and the ingester.
class NormalizedLocation(BaseModel):
    data_source_id: str
    data_source: str
    name: str
    lat: float
    lon: float
    address: Address
    contact: Contact
    services: list[Service]
    availability: Availability
    last_verified: str | None = None
