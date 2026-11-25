from typing import Any

from contracts.domain import Address, Availability, Contact, NormalizedLocation

from etl.base.normalizer import BaseNormalizer
from etl.dtos import RawLocation


def _clean(value: str | None) -> str | None:
    """Return the stripped value, or None if it is missing or blank."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _coordinates(payload: dict[str, Any]) -> tuple[float, float] | None:
    """
    Return an element's (lat, lon), or None if it has no coordinates.

    Nodes carry lat/lon directly. Ways and relations carry center.lat/center.lon,
    which Overpass adds because the query ends with `out center;`.
    """
    center = payload.get("center", {})
    lat = payload.get("lat", center.get("lat"))
    lon = payload.get("lon", center.get("lon"))
    if lat is None or lon is None:
        return None
    return lat, lon


def _address(tags: dict[str, str]) -> Address:
    """
    Build an Address from the addr:* tags, with missing parts as None.

    The street includes the house number when both are present (e.g. "12 Main Street").
    """
    street = _clean(tags.get("addr:street"))
    housenumber = _clean(tags.get("addr:housenumber"))
    if street and housenumber:
        street = f"{housenumber} {street}"
    return Address(
        street=street,
        city=_clean(tags.get("addr:city")),
        state=_clean(tags.get("addr:state")),
        postcode=_clean(tags.get("addr:postcode")),
    )


def _contact(tags: dict[str, str]) -> Contact:
    """
    Build a Contact from the phone and website tags, copied as-is.

    OSM treats `phone` and `contact:phone` (and `website` and `contact:website`)
    as the same. The bare tag is used when present; otherwise the `contact:` one.
    """
    return Contact(
        phone=_clean(tags.get("phone")) or _clean(tags.get("contact:phone")),
        website=_clean(tags.get("website")) or _clean(tags.get("contact:website")),
    )


def _availability(tags: dict[str, str]) -> Availability:
    """Build an Availability from the opening_hours tag, kept in OSM syntax."""
    return Availability(opening_hours=_clean(tags.get("opening_hours")))


class OpenStreetMapNormalizer(BaseNormalizer):
    """Map raw Overpass elements to NormalizedLocations."""

    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        """Normalize OSM elements, skipping any without a name or coordinates."""
        locations = (self._normalize_raw_location(raw) for raw in raw_locations)
        return [location for location in locations if location is not None]

    def _normalize_raw_location(
        self, raw_location: RawLocation
    ) -> NormalizedLocation | None:
        """
        Normalize one element, or return None if it has no name or coordinates.

        Services are left empty because they come from the query args, not the payload.
        """
        tags = raw_location.payload.get("tags", {})

        name = _clean(tags.get("name"))
        coordinates = _coordinates(raw_location.payload)
        if name is None or coordinates is None:
            return None
        lat, lon = coordinates

        return NormalizedLocation(
            data_source_id=raw_location.data_source_id,
            data_source=raw_location.data_source,
            name=name,
            lat=lat,
            lon=lon,
            address=_address(tags),
            contact=_contact(tags),
            services=[],
            availability=_availability(tags),
        )
