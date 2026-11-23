from contracts.domain import Location, LocationProvenance


def resolve_location_ids(
    merged_location: list[Location],
    merged_location_provenance: list[LocationProvenance],
    previous_location_provenance: list[LocationProvenance],
) -> tuple[list[Location], list[LocationProvenance]]:
    """Check if any incoming location provenance already exist in previous location provenance data store.
    -   If so, overwrite incoming location uid with existing location uid.
    -   Else, do nothing.
    """

    # If no previous location provenance, do nothing.
    if not previous_location_provenance:
        return merged_location, merged_location_provenance

    for location, location_provenance in zip(
        merged_location, merged_location_provenance
    ):
        for previous_lp in previous_location_provenance:
            # If existing previous location provenance, overwrite location id with existing location id.
            if location_provenance.source_to_id == previous_lp.source_to_id:
                location.id = previous_lp.location_id
                location_provenance.location_id = previous_lp.location_id
                break

    return merged_location, merged_location_provenance
