"""Field-level merging logic for combining locations from multiple sources."""

from contracts.domain import (
    Address,
    Availability,
    Contact,
    DataSource,
    NormalizedLocation,
    Service,
)

from etl.dtos import MatchGroup

# Source priority for most fields: prefer Google, fall back to OSM
SOURCE_PRIORITY = [DataSource.GOOGLE_PLACES, DataSource.OPENSTREETMAP]


def merge_group(group: MatchGroup) -> NormalizedLocation:
    """
    Merge a MatchGroup into a single NormalizedLocation.

    Applies field-level merge policies:
    - Most fields: first non-empty value in SOURCE_PRIORITY order
    - lat/lon: taken as a pair from one source (Google preferred)
    - address: taken as a unit from the source with more non-null components
    - services: union across sources, deduplicated
    - availability: prefer source with opening_hours (OSM preferred)
    - last_verified: latest date
    - data_source/data_source_id: from preferred source for stability

    Args:
        group: MatchGroup containing 1-2 NormalizedLocations keyed by source.

    Returns:
        Merged NormalizedLocation with the most complete data.
    """
    if len(group) == 1:
        # Single-source group, return as-is
        return list(group.values())[0]

    # Get locations in priority order
    locs = [group[src] for src in SOURCE_PRIORITY if src in group]

    # name: first non-empty
    name = next((loc.name for loc in locs if loc.name), "")

    # lat/lon: taken as a pair from one source (Google preferred for accuracy)
    coords_source = locs[0]
    lat = coords_source.lat
    lon = coords_source.lon

    # address: taken as a unit from the source with more non-null components
    address = _merge_address([loc.address for loc in locs])

    # contact: merged per subfield
    contact = _merge_contact([loc.contact for loc in locs])

    # services: union across sources, deduplicated
    services = _merge_services([loc.services for loc in locs])

    # availability: prefer source with opening_hours (OSM often has better hours data)
    availability = _merge_availability([loc.availability for loc in locs])

    # last_verified: latest date
    last_verified = _merge_last_verified([loc.last_verified for loc in locs])

    # data_source/data_source_id: from preferred source for output stability
    # TODO(stbrody): This is a bit of a lie since the data is actually a merger of both sources.
    # Consider introducing a new MergedLocation type that omits the source information, instead of
    # reusing NormalizedLocation.
    preferred = locs[0]
    data_source = preferred.data_source
    data_source_id = preferred.data_source_id

    return NormalizedLocation(
        data_source_id=data_source_id,
        data_source=data_source,
        name=name,
        lat=lat,
        lon=lon,
        address=address,
        contact=contact,
        services=services,
        availability=availability,
        last_verified=last_verified,
    )


def _merge_address(addresses: list[Address]) -> Address:
    """
    Merge addresses by taking the most complete one as a unit.

    Completeness is measured by number of non-null fields.
    This prevents mixing a street from one source with a postcode from another.
    """

    def completeness(addr: Address) -> int:
        return sum(
            1
            for field in [addr.street, addr.city, addr.state, addr.postcode]
            if field is not None
        )

    # Sort by completeness descending, take the most complete
    return max(addresses, key=completeness)


def _merge_contact(contacts: list[Contact]) -> Contact:
    """Merge contacts by taking first non-empty value per subfield."""
    return Contact(
        phone=next((c.phone for c in contacts if c.phone), None),
        email=next((c.email for c in contacts if c.email), None),
        website=next((c.website for c in contacts if c.website), None),
        social=next((c.social for c in contacts if c.social), None),
    )


def _merge_services(service_lists: list[list[Service]]) -> list[Service]:
    """
    Merge services by taking the union across sources, deduplicated.

    Different sources may infer different services from their tags,
    so we want to collect all of them. Deduplicate on (activity, item_category).
    """
    seen = set()
    merged = []

    for services in service_lists:
        for service in services:
            key = (service.activity, service.item_category)
            if key not in seen:
                seen.add(key)
                merged.append(service)

    # Sort for stable output
    merged.sort(key=lambda s: (s.activity.value, s.item_category.value))

    return merged


def _merge_availability(availabilities: list[Availability]) -> Availability:
    """
    Merge availability by preferring the one with opening_hours.
    """
    # First try to find one with opening_hours
    with_hours = next((a for a in availabilities if a.opening_hours), None)
    if with_hours:
        return with_hours

    # Otherwise take the first
    return availabilities[0]


def _merge_last_verified(dates: list[str | None]) -> str | None:
    """
    Merge last_verified dates by taking the latest.

    Assumes ISO date strings that sort lexicographically.
    """
    valid_dates = [d for d in dates if d is not None]
    if not valid_dates:
        return None

    return max(valid_dates)
