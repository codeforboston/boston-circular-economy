from datetime import datetime
from enum import Enum

from pydantic import BaseModel

"""
DTOs for the location pipeline.

The two pipeline boundaries are:
  - RawLocation: querier → normalizer
  - NormalizedLocation: normalizer → ingester

Everything else in this file is a supporting type for NormalizedLocation.
"""


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


# Activities describe what you can do at a location, from the visitor's perspective.
class Activity(str, Enum):
    REPAIR_FREE   = "repair_free"   # repair your items here for free (e.g. repair cafes)
    REPAIR_PAID   = "repair_paid"   # repair your items here for a fee
    DONATION_DROP = "donation_drop" # drop off items you no longer need
    DONATION_PICK = "donation_pick" # pick up free items (e.g. free stores, give-away shops)
    RESALE_BUY    = "resale_buy"    # buy secondhand items here
    RESALE_SELL   = "resale_sell"   # sell or consign your items here
    REFILL        = "refill"        # refill your own container here
    BORROWING     = "borrowing"     # borrow items here for free (e.g. tool libraries)
    RENTING       = "renting"       # rent items here for a fee
    LENDING       = "lending"       # lend your items out through this location


class ItemCategory(str, Enum):
    SHOES = "shoes"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    FURNITURE = "furniture"
    TOOLS = "tools"


class Service(BaseModel):
    activity: Activity
    item_category: ItemCategory


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
