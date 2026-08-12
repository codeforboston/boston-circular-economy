import os
from pathlib import Path

from etl.dtos import DataSource
from etl.local_data_store import LocalDataStore
from etl.merge_processor import MergeProcessor


def main() -> None:
    # reads normalized locations from the local store
    # writes merged locations back to the local store
    # Write data to the directory specified by the ETL_DATA_DIR env var, defaulting
    # to "data" under the current working directory if the env var is not set
    data_dir = Path(os.environ.get("ETL_DATA_DIR", "data"))
    store = LocalDataStore(data_dir)
    locations_by_source = {
        DataSource.GOOGLE_PLACES: store.read_source_snapshot(DataSource.GOOGLE_PLACES),
        DataSource.OPENSTREETMAP: store.read_source_snapshot(DataSource.OPENSTREETMAP),
    }
    merged_locations = MergeProcessor().process(locations_by_source)
    store.write_output_locations(merged_locations)

    print("merge-process-to-local finished")


if __name__ == "__main__":
    main()
