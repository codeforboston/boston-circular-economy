from __future__ import annotations

from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import os
from typing import Any

from base.querier import BaseQuerier
from dtos import RawLocation


GOOGLE_PLACES_ENDPOINT = "https://places.googleapis.com/v1/places:searchText"


class GooglePlacesQuerier(BaseQuerier):
    def __init__(self, *, api_key: str | None = None, text_query: str, data_source: str):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.text_query = text_query
        self.data_source = data_source

    def fetch(self) -> list[RawLocation]:
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required")

        payload = self._request({"textQuery": self.text_query})
        places = payload.get("places", [])
        fetched_at = datetime.now(timezone.utc)
        raw_locations: list[RawLocation] = []
        for index, place in enumerate(places):
            raw_locations.append(
                RawLocation(
                    data_source=self.data_source,
                    data_source_id=place.get("id") or f"{self.data_source}-{index}",
                    fetched_at=fetched_at,
                    payload=place,
                )
            )
        return raw_locations

    def _request(self, body: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            GOOGLE_PLACES_ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"Google Places request failed: {exc}") from exc


class GooglePlacesRepairQuerier(GooglePlacesQuerier):
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key, text_query="shoe repair Boston MA", data_source="google_places_repair")


class GooglePlacesDonationQuerier(GooglePlacesQuerier):
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key, text_query="donation centers Boston MA", data_source="google_places_donations")
