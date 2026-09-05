import json
from pathlib import Path

from etl.base.data_store import BaseDataStore
from etl.dtos import DataSource, NormalizedLocation

loc_key = "locations"


# Reads and writes normalized locations to a local file.
class LocalDataStore(BaseDataStore):
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.snapshots_dir = data_dir / "snapshots"
        self.output_dir = data_dir / "output"

    def write_source_snapshot(
        self,
        source: DataSource,
        normalized_locations: list[NormalizedLocation],
    ) -> None:
        file_path = self._get_snapshot_path(source)
        self._write_locations(file_path, normalized_locations)

    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        file_path = self._get_snapshot_path(source)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        with open(file_path) as file:
            snapshot_serialized = json.load(file)

        return [
            NormalizedLocation.model_validate(location)
            for location in snapshot_serialized[loc_key]
        ]

    def write_output_locations(
        self,
        output_locations: list[NormalizedLocation],
    ) -> None:
        file_path = self.output_dir / "locations.json"
        self._write_locations(file_path, output_locations)

    def _write_locations(
        self,
        file_path: Path,
        locations: list[NormalizedLocation],
    ) -> None:
        locations_serialized = [
            location.model_dump(mode="json") for location in locations
        ]
        payload = {loc_key: locations_serialized}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            file.write(json.dumps(payload, indent=2))

    def _get_snapshot_path(self, source: DataSource) -> Path:
        return self.snapshots_dir / f"{source.value}_snapshot.json"
