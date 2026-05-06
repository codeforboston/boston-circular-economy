from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dtos import Activity, Address, Availability, Contact, ItemCategory, Service


@dataclass(frozen=True)
class GooglePlacesQuery:
    text_query: str
    data_source: str
    item_category: ItemCategory
    activity: Activity


def extract_postcode(formatted_address: str | None) -> str | None:
    if not formatted_address:
        return None
    parts = formatted_address.split()
    for part in parts:
        if len(part) == 5 and part.isdigit():
            return part
    return None


def normalize_google_place(
    raw: dict[str, Any],
    *,
    data_source: str,
    data_source_id: str,
    item_category: ItemCategory,
    activity: Activity,
) -> dict[str, Any]:
    display_name = raw.get("displayName") or {}
    formatted_address = raw.get("formattedAddress")
    location = raw.get("location") or {}
    return {
        "data_source_id": data_source_id,
        "data_source": data_source,
        "name": display_name.get("text") or data_source_id,
        "lat": location.get("latitude", 0.0),
        "lon": location.get("longitude", 0.0),
        "address": Address(
            street=formatted_address,
            postcode=extract_postcode(formatted_address),
        ),
        "contact": Contact(),
        "services": [Service(activity=activity, item_category=item_category)],
        "availability": Availability(),
    }
