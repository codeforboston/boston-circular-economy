from datetime import datetime, timezone
import httpx, time
from etl.base.querier import BaseQuerier
from etl.dtos import DataSource, RawLocation

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Overpass asks clients to identify themselves.
USER_AGENT = "boston-circular-economy-etl/0.1 (https://github.com/codeforboston/boston-circular-economy)"
# sometimes the Overpass API is overloaded or the server times out, so we retry a few times. 429 = too many requests, 502/503/504 = server error.
RETRYABLE = {429, 502, 503, 504}


DEFAULT_BBOX = (42.2, -71.2, 42.5, -70.9)  # south, west, north, east


class OpenStreetMapQuerier(BaseQuerier):

    def __init__(self, tag_filters: list[str], bbox=DEFAULT_BBOX, timeout_s: int = 60):
        # tag_filters are Overpass selector strings, e.g. '["shop"="tailor"]'
        self.tag_filters = tag_filters
        self.bbox = bbox
        self.timeout_s = timeout_s

    def fetch(self) -> list[RawLocation]:
        query = self._build_query()
        elements = self._run(query)
        return self._to_raw_locations(elements)

    def _build_query(self) -> str:
        s, w, n, e = self.bbox
        bbox = f"({s},{w},{n},{e})"
        lines = "".join(f"nwr{f}{bbox};" for f in self.tag_filters)
        return f"[out:json][timeout:{self.timeout_s}];({lines});out center;"

    def _run(self, query: str, attempts: int = 3) -> list[dict]:
        for attempt in range(attempts):
            response = httpx.post(
                OVERPASS_URL, data={"data": query},
                timeout=self.timeout_s + 10,
                headers={"User-Agent": USER_AGENT},
            )
            if response.status_code == 200:
                body = response.json()
                return body["elements"]
            if response.status_code in RETRYABLE and attempt < attempts - 1:
                time.sleep(2 ** attempt * 5)   # 5s, 10s
                continue
            raise RuntimeError(f"Overpass returned {response.status_code}: {response.text[:500]}")

    def _to_raw_locations(self, elements: list[dict]) -> list[RawLocation]:
        now = datetime.now(timezone.utc)
        by_id: dict[str, RawLocation] = {}
        for el in elements:
            key = f"{el['type']}/{el['id']}"          # stable native ID
            by_id[key] = RawLocation(                 # dict = dedup by ID
                data_source=DataSource.OPENSTREETMAP,
                data_source_id=key,
                fetched_at=now,
                payload=el,
            )
        return list(by_id.values())
