import pytest
from contracts.domain import Activity, DataSource, ItemCategory, Service, ServiceClaim

from etl.service_claims import build_service_claims
from etl.sources.google_places.queries import GOOGLE_PLACES_QUERY_ARGS
from etl.sources.openstreetmap.queries import OPENSTREETMAP_QUERY_ARGS

REPAIR_CLOTHING = Service(activity=Activity.REPAIR_PAID, item_category=ItemCategory.CLOTHING)
RESALE_CLOTHING = Service(activity=Activity.RESALE_BUY, item_category=ItemCategory.CLOTHING)


def test_one_claim_per_location_and_service(make_location):
    first_location = make_location(data_source_id="a")
    second_location = make_location(data_source_id="b")

    claims = build_service_claims(
        [first_location, second_location], [REPAIR_CLOTHING, RESALE_CLOTHING]
    )

    assert claims == [
        ServiceClaim(
            data_source=DataSource.GOOGLE_PLACES,
            data_source_id="a",
            activity=Activity.REPAIR_PAID,
            item_category=ItemCategory.CLOTHING,
        ),
        ServiceClaim(
            data_source=DataSource.GOOGLE_PLACES,
            data_source_id="a",
            activity=Activity.RESALE_BUY,
            item_category=ItemCategory.CLOTHING,
        ),
        ServiceClaim(
            data_source=DataSource.GOOGLE_PLACES,
            data_source_id="b",
            activity=Activity.REPAIR_PAID,
            item_category=ItemCategory.CLOTHING,
        ),
        ServiceClaim(
            data_source=DataSource.GOOGLE_PLACES,
            data_source_id="b",
            activity=Activity.RESALE_BUY,
            item_category=ItemCategory.CLOTHING,
        ),
    ]


def test_claims_keep_the_location_source(make_location):
    location = make_location(data_source=DataSource.OPENSTREETMAP)

    [claim] = build_service_claims([location], [REPAIR_CLOTHING])

    assert claim.data_source == DataSource.OPENSTREETMAP
    assert claim.data_source_id == location.data_source_id


def test_no_locations_gives_no_claims():
    assert build_service_claims([], [REPAIR_CLOTHING]) == []


# Claims come from a query's services, so a query without services would
# write locations that offer nothing.
@pytest.mark.parametrize(
    "query_args", GOOGLE_PLACES_QUERY_ARGS + OPENSTREETMAP_QUERY_ARGS
)
def test_every_query_has_services(query_args):
    assert query_args["services"]
