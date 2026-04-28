import json
from pathlib import Path

from base.ingester import BaseIngester
from dtos import NormalizedLocation


class JSONIngester(BaseIngester):

    def __init__(self, output_path: Path):
        self.output_path = output_path

    def ingest(self, normalized_locations: list[NormalizedLocation]) -> None:
        # read existing records
        existing = []
        if self.output_path.exists():
            with open(self.output_path) as f:
                existing = json.load(f)

        # convert new records to dicts
        new_records = [location.model_dump() for location in normalized_locations]

        # merge by data_source + data_source_id
        merged = {
            (r["data_source"], r["data_source_id"]): r for r in existing
        }
        merged.update({
            (r["data_source"], r["data_source_id"]): r for r in new_records
        })

        with open(self.output_path, "w") as f:
            json.dump(list(merged.values()), f, indent=2, default=str)
