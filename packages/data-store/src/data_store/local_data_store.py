import json
from pathlib import Path

from contracts.domain import DataSource, NormalizedLocation, ServiceClaim

from data_store.base import BaseDataStore

loc_key = "locations"
service_claims_key = "service_claims"


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
        existing_locations = (
            self._read_locations(file_path) if file_path.exists() else []
        )
        merged_locations = {
            location.data_source_id: location
            for location in [*existing_locations, *normalized_locations]
        }
        self._write_locations(file_path, list(merged_locations.values()))

    def read_source_snapshot(
        self,
        source: DataSource,
    ) -> list[NormalizedLocation]:
        file_path = self._get_snapshot_path(source)
        return self._read_locations(file_path)

    def write_service_claims(
        self,
        service_claims: list[ServiceClaim],
    ) -> None:
        file_path = self._get_service_claims_path()
        existing_claims = (
            self.read_service_claims() if file_path.exists() else []
        )
        # A claim has no fields beyond its identity, so writing an existing
        # claim again keeps one copy instead of adding a duplicate.
        merged_claims = {
            (
                claim.data_source,
                claim.data_source_id,
                claim.activity,
                claim.item_category,
            ): claim
            for claim in [*existing_claims, *service_claims]
        }
        claims_serialized = [
            claim.model_dump(mode="json") for claim in merged_claims.values()
        ]
        payload = {service_claims_key: claims_serialized}

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            file.write(json.dumps(payload, indent=2))

    def read_service_claims(self) -> list[ServiceClaim]:
        file_path = self._get_service_claims_path()
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        with open(file_path, "r") as file:
            claims_serialized = json.load(file)

        return [
            ServiceClaim.model_validate(claim)
            for claim in claims_serialized[service_claims_key]
        ]

    def read_output_locations(self) -> list[NormalizedLocation]:
        file_path = self.output_dir / "locations.json"
        return self._read_locations(file_path)

    def _read_locations(self, file_path: Path) -> list[NormalizedLocation]:
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        with open(file_path, "r") as file:
            locations_serialized = json.load(file)

        return [
            NormalizedLocation.model_validate(location)
            for location in locations_serialized[loc_key]
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
        locations_serialized = [location.model_dump(mode="json") for location in locations]
        payload = { loc_key: locations_serialized }

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file:
            file.write(json.dumps(payload, indent=2))

    def _get_snapshot_path(self, source: DataSource) -> Path:
        return self.snapshots_dir / f"{source.value}_snapshot.json"

    def _get_service_claims_path(self) -> Path:
        return self.snapshots_dir / "service_claims.json"
