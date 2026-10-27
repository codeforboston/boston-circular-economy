from typing import Literal

from contracts.domain import Address, Availability, Contact, NormalizedLocation, Service
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Location identifier in the form '<data_source>:<data_source_id>'. "
        ),
    )
    name: str
    lat: float
    lon: float
    address: Address
    services: list[Service]
    contact: Contact
    availability: Availability
    last_verified: str | None = None

    @classmethod
    def from_location(cls, location: NormalizedLocation) -> "SearchResult":
        return cls(
            id=f"{location.data_source.value}:{location.data_source_id}",
            **location.model_dump(),
        )

class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(
        default_factory=list,
        description="A list of search results matching the search criteria.",
    )

class FeedbackInput(BaseModel):
    reaction: Literal["like", "dislike"] = Field(
        ..., description="The user's reaction, either 'like' or 'dislike'."
    )
    message: str | None = Field(
        default=None, description="The feedback message from the user."
    )
