import httpx
import pytest

from etl.sources.openstreetmap.querier import OpenStreetMapQuerier

from etl.sources.openstreetmap.querier import RETRYABLE, OverpassError


@pytest.fixture
def clothing_filters():
    return [
        '["shop"="tailor"]',
        '["craft"="tailor"]',
        '["shop"="second_hand"]',
        '["shop"="clothes"]["second_hand"="yes"]',
        '["shop"="charity"]',
        '["amenity"="recycling"]["recycling:clothes"="yes"]',
    ]


@pytest.fixture
def querier(clothing_filters):
    return OpenStreetMapQuerier(tag_filters=clothing_filters)


@pytest.fixture(scope="session")
def fetch_or_skip():
    """Run `querier.fetch()` against live Overpass, skipping the test if Overpass is flaky.

    Overpass is often overloaded or slow, which says nothing about our code, so
    those failures skip (inconclusive) instead of failing. Any other error,
    e.g. a 400 from a malformed query, still fails the test.
    """
    def _fetch(querier):
        try:
            return querier.fetch()
        except OverpassError as e:
            if e.status_code in RETRYABLE:
                pytest.skip(f"Overpass unavailable after retries: {e}")
            raise
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            pytest.skip(f"Overpass unreachable: {e!r}")

    return _fetch