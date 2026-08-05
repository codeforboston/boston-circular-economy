from etl.base.data_store import BaseDataStore
from etl.dtos import DataSource, NormalizedLocation
from pathlib import Path
import json

src_key = 'source'
loc_key = 'locations'
data_dir = Path(__file__).parent / "data"
snapshots_dir = data_dir / "snapshots"
output_dir = data_dir / "output"

# Reads and writes normalized locations to a local file.
class LocalDataStore(BaseDataStore):

    def write_source_snapshot(
        self,
        source: DataSource,
        normalized_locations: list[NormalizedLocation],
    ) -> None:
        file_path = self._get_snapshot_path(source)
        self._write_locations(file_path, normalized_locations, source=source)

    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        file_path = self._get_snapshot_path(source)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        with open(file_path, "r") as file:
            snapshot_serialized = json.load(file)

        snapshot_source = snapshot_serialized[src_key]
        if snapshot_source != source.value:
            raise ValueError(f"Provided source '{source.value}' does not match file source '{snapshot_source}'")

        return [NormalizedLocation.model_validate(location) for location in snapshot_serialized[loc_key]]

    def write_output_locations(
        self,
        output_locations: list[NormalizedLocation],
    ) -> None:
        file_path = output_dir / "locations.json"
        self._write_locations(file_path, output_locations)

    def _write_locations(
        self,
        file_path: Path,
        locations: list[NormalizedLocation],
        source: DataSource | None = None,
    ) -> None:
        locations_serialized = [location.model_dump(mode="json") for location in locations]
        payload: dict = { loc_key: locations_serialized }
        if source is not None:
            payload[src_key] = source.value

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            file.write(json.dumps(payload, indent=2))

    def _get_snapshot_path(self, source: DataSource) -> Path:
        return snapshots_dir / f"{source.value}_snapshot.json"
