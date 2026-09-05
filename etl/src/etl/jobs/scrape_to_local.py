import os
from pathlib import Path

from etl.dtos import DataSource
from etl.local_data_store import LocalDataStore
from etl.sources.google_places.normalizer import GooglePlacesNormalizer
from etl.sources.google_places.querier import GooglePlacesQuerier
from etl.sources.openstreetmap.normalizer import OpenStreetMapNormalizer
from etl.sources.openstreetmap.querier import OpenStreetMapQuerier

google_places_query_args: list[dict[str, str]] = []
openstreetmap_query_args: list[dict[str, str]] = []


def main() -> None:
    # reads and writes normalized locations to the local output file
    # Write data to the directory specified by the ETL_DATA_DIR env var, defaulting
    # to "data" under the current working directory if the env var is not set
    data_dir = Path(os.environ.get("ETL_DATA_DIR", "data"))
    store = LocalDataStore(data_dir)

    for _args in google_places_query_args:
        # queries the Google Places API
        querier = GooglePlacesQuerier()
        raw_locations = querier.fetch()

        # maps Google Places payloads to the shared schema
        normalizer = GooglePlacesNormalizer()
        normalized_locations = normalizer.normalize(raw_locations)

        # writes the normalized locations to the local output file
        store.write_source_snapshot(DataSource.GOOGLE_PLACES, normalized_locations)

    for _args in openstreetmap_query_args:
        # queries the OpenStreetMap API
        querier = OpenStreetMapQuerier()
        raw_locations = querier.fetch()

        # maps OpenStreetMap payloads to the shared schema
        normalizer = OpenStreetMapNormalizer()
        normalized_locations = normalizer.normalize(raw_locations)

        # writes the normalized locations to the local output file
        store.write_source_snapshot(DataSource.OPENSTREETMAP, normalized_locations)

    print("scrape-to-local finished")


if __name__ == "__main__":
    main()
