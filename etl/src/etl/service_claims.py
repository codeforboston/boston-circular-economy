from contracts.domain import NormalizedLocation, Service, ServiceClaim


def build_service_claims(
    locations: list[NormalizedLocation],
    services: list[Service],
) -> list[ServiceClaim]:
    """
    Claim that every location returned by a query offers every service of that query.

    The query, not the location record, says what a place offers. A search for
    tailors, for example, returns places that repair clothing.
    """
    return [
        ServiceClaim(
            data_source=location.data_source,
            data_source_id=location.data_source_id,
            activity=service.activity,
            item_category=service.item_category,
        )
        for location in locations
        for service in services
    ]
