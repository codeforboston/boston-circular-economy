import os
from pathlib import Path

from contracts.domain import DataSource
from data_store import LocalDataStore

from etl.merge_processor import MergeProcessor
from etl.resolve_id import resolve_location_ids


def main() -> None:
    # Reads NormalizedLocation source snapshots and writes final Location output.
    # Write data to the directory specified by the ETL_DATA_DIR env var, defaulting
    # to "data" under the current working directory if the env var is not set
    data_dir = Path(os.environ.get("ETL_DATA_DIR", "data"))
    store = LocalDataStore(data_dir)
    locations_by_source = {
        DataSource.GOOGLE_PLACES: store.read_source_snapshot(DataSource.GOOGLE_PLACES),
        DataSource.OPENSTREETMAP: store.read_source_snapshot(DataSource.OPENSTREETMAP),
    }
    merged_locations, merged_locations_provenance = MergeProcessor().process(locations_by_source)

    # Lookup existing LocationProvenance data store:
    #   - If any existing Location has same provenance, reuse that Location.id
    merged_locations, merged_locations_provenance = resolve_location_ids(
        merged_locations, 
        merged_locations_provenance,
        previous_location_provenance=store.read_location_provenance())

    store.write_location_provenance(merged_locations_provenance)
    store.write_output_locations(merged_locations)

    print("merge-process-to-local finished")


if __name__ == "__main__":
    main()
