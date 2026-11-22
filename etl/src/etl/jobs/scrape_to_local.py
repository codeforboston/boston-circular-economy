import os
from pathlib import Path

from contracts.domain import DataSource
from data_store import LocalDataStore

from etl.sources.google_places.normalizer import GooglePlacesNormalizer
from etl.sources.google_places.querier import GooglePlacesQuerier
from etl.sources.google_places.queries import GOOGLE_PLACES_QUERY_ARGS
from etl.sources.openstreetmap.normalizer import OpenStreetMapNormalizer
from etl.sources.openstreetmap.querier import OpenStreetMapQuerier
from etl.sources.openstreetmap.queries import OPENSTREETMAP_QUERY_ARGS


def main() -> None:
    # reads and writes normalized locations to the local output file
    # Write data to the directory specified by the ETL_DATA_DIR env var, defaulting
    # to "data" under the current working directory if the env var is not set
    data_dir = Path(os.environ.get("ETL_DATA_DIR", "data"))
    store = LocalDataStore(data_dir)

    for query_args in GOOGLE_PLACES_QUERY_ARGS:
        # queries the Google Places API
        querier = GooglePlacesQuerier(**query_args["querier"])
        raw_locations = querier.fetch()

        # maps Google Places payloads to the shared schema
        normalizer = GooglePlacesNormalizer()
        normalized_locations = normalizer.normalize(raw_locations)

        # writes the normalized locations to the local output file
        store.write_source_snapshot(DataSource.GOOGLE_PLACES, normalized_locations)

    for query_args in OPENSTREETMAP_QUERY_ARGS:
        # queries the OpenStreetMap API
        querier = OpenStreetMapQuerier(**query_args["querier"])
        raw_locations = querier.fetch()

        # maps OpenStreetMap payloads to the shared schema
        normalizer = OpenStreetMapNormalizer()
        normalized_locations = normalizer.normalize(raw_locations)

        # writes the normalized locations to the local output file
        store.write_source_snapshot(DataSource.OPENSTREETMAP, normalized_locations)

    print("scrape-to-local finished")


if __name__ == "__main__":
    main()
