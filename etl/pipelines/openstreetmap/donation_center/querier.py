from base.querier import BaseQuerier
from dtos import RawLocation
from pipelines.openstreetmap.openstreetmap_common import (
    GREATER_BOSTON_BBOX,
    fetch_overpass,
)


DATA_SOURCE = "openstreetmap_donation"

OVERPASS_QUERY = f"""
[out:json][timeout:25];
(
  nwr["shop"="charity"]({GREATER_BOSTON_BBOX});
  nwr["amenity"="recycling"]["recycling_type"="centre"]({GREATER_BOSTON_BBOX});
  nwr["amenity"="social_facility"]["social_facility"="food_bank"]({GREATER_BOSTON_BBOX});
);
out center;
"""


class DonationCenterQuerier(BaseQuerier):

    def fetch(self) -> list[RawLocation]:
        return fetch_overpass(OVERPASS_QUERY, DATA_SOURCE)
