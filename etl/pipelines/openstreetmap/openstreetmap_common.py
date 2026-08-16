import json
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dtos import (
    Activity,
    Address,
    Availability,
    Contact,
    ItemCategory,
    NormalizedLocation,
    RawLocation,
    Service,
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GREATER_BOSTON_BBOX = "42.2,-71.2,42.5,-70.9"

# OSM shop= values mapped to the ItemCategory of the goods sold/serviced.
SHOP_TO_CATEGORY: dict[str, ItemCategory] = {
    "tailor": ItemCategory.CLOTHING,
    "clothes": ItemCategory.CLOTHING,
    "shoes": ItemCategory.SHOES,
    "computer": ItemCategory.ELECTRONICS,
    "electronics": ItemCategory.ELECTRONICS,
    "mobile_phone": ItemCategory.ELECTRONICS,
    "furniture": ItemCategory.FURNITURE,
    "books": ItemCategory.BOOKS,
    "tool_hire": ItemCategory.TOOLS,
    "hardware": ItemCategory.TOOLS,
}

def fetch_overpass(query: str, data_source: str) -> list[RawLocation]:
    """POST an Overpass QL query and wrap each element as a RawLocation."""
    body = urlencode({"data": query}).encode("utf-8")
    request = Request(
        OVERPASS_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "boston-circular-economy-etl/0.1",
        },
    )
    with urlopen(request, timeout=60) as response:
        data = json.load(response)

    fetched_at = datetime.now(timezone.utc)
    raw_locations = []
    for element in data.get("elements", []):
        raw_locations.append(RawLocation(
            data_source=data_source,
            data_source_id=f"osm-{element['type']}-{element['id']}",
            fetched_at=fetched_at,
            payload=element,
        ))
    return raw_locations


def build_normalized_location(
    raw: RawLocation,
    data_source: str,
    get_activities: Callable[[dict], list[Activity]],
) -> NormalizedLocation | None:
    """Validate an Overpass element and assemble a NormalizedLocation.

    Returns None if the element lacks a name, coordinates, or services.
    """
    element = raw.payload
    tags = element.get("tags", {})

    name = tags.get("name")
    lat, lon = get_coordinates(element)
    categories = infer_item_categories(tags)
    if not name or lat is None or lon is None or not categories:
        return None

    activities = get_activities(tags)
    services = [
        Service(activity=activity, item_category=category)
        for activity in activities
        for category in categories
    ]

    return NormalizedLocation(
        data_source_id=raw.data_source_id,
        data_source=data_source,
        name=name,
        lat=lat,
        lon=lon,
        address=build_address(tags),
        contact=build_contact(tags),
        services=services,
        availability=build_availability(tags),
        last_verified=tags.get("check_date"),
    )


def get_coordinates(element: dict) -> tuple[float | None, float | None]:
    target = element if element["type"] == "node" else element.get("center", {})
    return target.get("lat"), target.get("lon")


def build_address(tags: dict) -> Address:
    houseNumber = tags.get("addr:housenumber")
    street_name = tags.get("addr:street")
    if houseNumber and street_name:
        street = f"{houseNumber} {street_name}"
    else:
        street = street_name or houseNumber
    return Address(
        street=street,
        city=tags.get("addr:city"),
        state=tags.get("addr:state"),
        postcode=tags.get("addr:postcode"),
    )


def build_contact(tags: dict) -> Contact:
    return Contact(
        phone=tags.get("phone") or tags.get("contact:phone"),
    #investigate
        email=tags.get("email") or tags.get("contact:email"),
        website=tags.get("website") or tags.get("contact:website"),
    )


def build_availability(tags: dict) -> Availability:
    return Availability(opening_hours=tags.get("opening_hours"))

# not great
def infer_item_categories(tags: dict) -> list[ItemCategory]:
    """Infer item categories from shop type and free-text fields."""
    categories: set[ItemCategory] = set()

    #investigate
    shop = tags.get("shop")
    category = SHOP_TO_CATEGORY.get(shop)
    if category:
        categories.add(category)

    text = " ".join([
        tags.get("name", ""),
        #investigate
        tags.get("name:en", ""),
        tags.get("description", ""),
    ]).lower()

    keyword_map = {
        ItemCategory.CLOTHING: ["clothing", "clothes", "apparel", "tailor"],
        ItemCategory.ELECTRONICS: ["electronics", "computer", "phone", "printer"],
        ItemCategory.FURNITURE: ["furniture"],
        ItemCategory.SHOES: ["shoe", "cobbler"],
        ItemCategory.BOOKS: ["book"],
        ItemCategory.TOOLS: ["tool"],
    }
    for category, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            categories.add(category)

    return sorted(categories, key=lambda c: c.value)
