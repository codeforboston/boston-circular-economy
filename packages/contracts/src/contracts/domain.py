from enum import Enum

from pydantic import BaseModel


class Address(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postcode: str | None = None


# Activities describe what you can do at a location, from the visitor's perspective.
class Activity(str, Enum):
    REPAIR_FREE = "repair_free"  # repair your items here for free (e.g. repair cafes)
    REPAIR_PAID = "repair_paid"  # repair your items here for a fee
    DONATION_DROP = "donation_drop"  # drop off items you no longer need
    DONATION_PICK = "donation_pick"  # pick up free items (e.g. free stores, give-away shops)
    RESALE_BUY = "resale_buy"  # buy secondhand items here
    RESALE_SELL = "resale_sell"  # sell or consign your items here
    REFILL = "refill"  # refill your own container here
    BORROWING = "borrowing"  # borrow items here for free (e.g. tool libraries)
    RENTING = "renting"  # rent items here for a fee
    LENDING = "lending"  # lend your items out through this location

class Contact(BaseModel):
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    social: str | None = None


# The supported data sources for local service providers.
class DataSource(str, Enum):
    GOOGLE_PLACES = "google_places"
    OPENSTREETMAP = "openstreetmap"


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

class NormalizedLocation(BaseModel):
    """A source-specific record produced by a normalizer in etl."""

    # Source specific id
    data_source_id: str 
    data_source: DataSource
    # Info
    name: str
    lat: float
    lon: float
    address: Address
    contact: Contact
    services: list[Service]
    availability: Availability
    last_verified: str | None = None


class Location(BaseModel):
    """Final location to persist to data store and shared across the application (client, server etc.)."""
    # Application-wide unique id
    id: str
    # Info
    name: str
    lat: float
    lon: float
    address: Address
    contact: Contact
    services: list[Service]
    availability: Availability
    last_verified: str | None = None

class LocationProvenance(BaseModel):
    """Linker table linking Location id to its source (NormalizedLocation) id."""
    location_id: str
    source_to_id: dict[DataSource, str] # key: data source, val: data_source_id

# ServiceClaim says one location offers one service. Locations and claims are
# stored separately because a location's services come from the query that
# found it, not from the location record itself.
class ServiceClaim(BaseModel):
    data_source: DataSource
    data_source_id: str  # the claimed location's id within its data source
    activity: Activity
    item_category: ItemCategory
