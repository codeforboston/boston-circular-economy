#!/usr/bin/env python3
"""
Transform OSM Overpass API data into the Circular Economy Source Schema.

Reads:  broad-search-00.json  (raw Overpass response)
Writes: sources.json  (array of source objects)

No external dependencies — uses only Python stdlib.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "broad-search-00.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "sources.json")

# ── Mapping tables ──────────────────────────────────────────────────────────

ACTIVITY_MAP = {
    "charity": {"donate", "resell"},
    "second_hand": {"resell", "reuse"},
    "tailor": {"alter", "repair"},
    "repair": {"repair"},
    "tyres": {"repair"},
    "computer": set(),
    "musical_instrument": set(),
}

MATERIAL_MAP = {
    "tailor": {"clothing"},
    "computer": {"electronics"},
    "tyres": {"tires"},
    "musical_instrument": {"musical_instruments"},
}

# Keywords scanned in name / name:en / description to add material categories
MATERIAL_KEYWORDS = {
    "clothing": ["clothing", "clothes", "apparel", "fashion", "vintage", "consignment"],
    "electronics": ["electronics", "computer", "printer", "typewriter", "fax"],
    "furniture": ["furniture"],
    "appliances": ["appliance"],
    "art_supplies": ["art supply", "art supplies", "craft supply", "craft supplies"],
    "tires": ["tire", "tyre"],
    "musical_instruments": ["musical instrument", "guitar", "music"],
}


def infer_activities(tags: dict) -> list[str]:
    """Derive circular_activities from OSM tags."""
    activities: set[str] = set()
    shop = tags.get("shop", "")

    # From shop type
    activities.update(ACTIVITY_MAP.get(shop, set()))

    # Explicit repair tag (yes, or semicolon-delimited value like "pump;motor")
    repair_val = tags.get("repair", "")
    if repair_val and repair_val != "no":
        activities.add("repair")

    # second_hand tag
    if tags.get("second_hand") in ("yes", "only"):
        activities.add("resell")
        activities.add("reuse")

    # rental tag
    if tags.get("rental") == "yes":
        activities.add("rent")

    return sorted(activities)


def infer_materials(tags: dict) -> list[str]:
    """Derive material_categories from OSM tags."""
    materials: set[str] = set()
    shop = tags.get("shop", "")

    # From shop type
    materials.update(MATERIAL_MAP.get(shop, set()))

    # Keyword scan across name, name:en, and description
    text = " ".join(
        [
            tags.get("name", ""),
            tags.get("name:en", ""),
            tags.get("description", ""),
        ]
    ).lower()

    for category, keywords in MATERIAL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            materials.add(category)

    return sorted(materials)


def build_address(tags: dict) -> dict:
    """Build address sub-object from addr:* tags."""
    housenumber = tags.get("addr:housenumber")
    street_name = tags.get("addr:street")

    if housenumber and street_name:
        street = f"{housenumber} {street_name}"
    elif street_name:
        street = street_name
    elif housenumber:
        street = housenumber
    else:
        street = None

    return {
        "street": street,
        "city": tags.get("addr:city"),
        "state": tags.get("addr:state"),
        "postcode": tags.get("addr:postcode"),
    }


def build_contact(tags: dict) -> dict:
    """Build contact sub-object from phone/email/website/social tags."""
    phone = tags.get("phone") or tags.get("contact:phone")
    email = tags.get("email")
    website = tags.get("website") or tags.get("contact:website")

    social = {}
    fb = tags.get("contact:facebook")
    ig = tags.get("contact:instagram")
    if fb:
        social["facebook"] = fb
    if ig:
        social["instagram"] = ig

    return {
        "phone": phone,
        "email": email,
        "website": website,
        "social": social or None,
    }


def osm_to_source(element: dict) -> dict:
    """Transform one OSM element into a circular economy source."""
    tags = element.get("tags", {})
    etype = element["type"]
    eid = element["id"]

    # Coordinates
    if etype == "node":
        lat, lon = element["lat"], element["lon"]
    else:
        lat = element["center"]["lat"]
        lon = element["center"]["lon"]

    # Last verified
    last_verified = tags.get("check_date") or tags.get("check_date:opening_hours")

    return {
        "source_id": f"osm-{etype}-{eid}",
        "source_type": "organization",
        "name": tags.get("name"),
        "lat": lat,
        "lon": lon,
        "address": build_address(tags),
        "contact": build_contact(tags),
        "circular_activities": infer_activities(tags),
        "material_categories": infer_materials(tags),
        "availability": {
            "opening_hours": tags.get("opening_hours"),
            "is_persistent": True,
        },
        "accessibility": {
            "wheelchair": tags.get("wheelchair", "unknown"),
        },
        "brand": tags.get("brand"),
        "operator": tags.get("operator"),
        "osm_id": eid,
        "last_verified": last_verified,
    }


def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    sources = [osm_to_source(el) for el in data["elements"]]

    with open(OUTPUT_FILE, "w") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)

    print(f"Transformed {len(sources)} elements → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
